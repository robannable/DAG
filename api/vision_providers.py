"""Vision-enhanced API provider functions - Anthropic, or OpenRouter image-capable models"""
import logging
from typing import Dict, Any, List, Optional, Iterator
from api.retry import RetryConfig
from api.providers import (
    ErrorChunk,
    auth_headers,
    resolve_temperature,
    stream_response,
)


# Static instruction scaffolding for the vision path. Kept as a single
# constant so it forms a byte-identical cache_control prefix on every request;
# the per-call user message carries only the images and dynamic project text.
VISION_SYSTEM_PROMPT = """You are a dramaturgical expert that creates diegetic artefacts for architectural projects.

You will be provided with visual materials (sketches, diagrams, photographs, or reference images) along with text descriptions.

Structure every response in this order:

1. First, carefully analyze the provided images and share that analysis within <think> tags. Consider:
   - Spatial organization, layout, and relationships
   - Annotations, labels, or handwritten notes (OCR)
   - Material indications and aesthetic qualities
   - Scale, proportion, and atmospheric intentions
   - Site context and environmental factors
   - Any diagrams or visual information systems
The <think> section will not be visible to the end user unless they choose to see it.

2. Explain (100-150 words) your choice of specific artefact within the given category, informed by both visuals and text.
3. Summarize (2-3 sentences) how this artefact relates to the project's themes and visual context.
4. Pose 2-3 thought-provoking questions about the relationship between this artefact and the architecture project.
5. Create the diegetic artefact itself (500-750 words) using markdown. Reference specific elements you observed in the visual materials (spaces, annotations, materials, dimensions) so the artefact feels grounded in the actual visual context rather than generic assumptions."""


def _vision_intro(images: List[dict], text_prompt: str) -> str:
    return (
        f"Please analyze the {len(images)} image(s) shared above and use that "
        f"visual context together with the project details below.\n\n{text_prompt}"
    )


def prepare_vision_request_anthropic(
    text_prompt: str,
    images: List[dict],
    model_config: Dict[str, Any],
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """
    Prepare vision request for Anthropic Claude

    Args:
        text_prompt: Dynamic, per-request project text (static instructions
            live in VISION_SYSTEM_PROMPT)
        images: List of image data with base64 and media_type
        model_config: Model configuration
        temperature: Optional temperature override

    Returns:
        Request data dictionary
    """
    # Build content array: images first, then the dynamic text prompt
    content = []

    for img in images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img['media_type'],
                "data": img['base64']
            }
        })

    content.append({"type": "text", "text": _vision_intro(images, text_prompt)})

    data = {
        "model": model_config["model"],
        "max_tokens": model_config["max_tokens"],
        "stream": True,
        "system": [
            {
                "type": "text",
                "text": VISION_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }
    temp = resolve_temperature(model_config, temperature)
    if temp is not None:
        data["temperature"] = temp
    if model_config.get("thinking"):
        data["thinking"] = model_config["thinking"]
    return data


def prepare_vision_request_openrouter(
    text_prompt: str,
    images: List[dict],
    model_config: Dict[str, Any],
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """Prepare an OpenAI-format vision request for OpenRouter.

    Images travel as base64 data URLs in ``image_url`` parts, ahead of the
    text part.
    """
    content = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:{img['media_type']};base64,{img['base64']}"}
        }
        for img in images
    ]
    content.append({"type": "text", "text": _vision_intro(images, text_prompt)})

    data = {
        "model": model_config["model"],
        "max_tokens": model_config["max_tokens"],
        "stream": True,
        "messages": [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    }
    temp = resolve_temperature(model_config, temperature)
    if temp is not None:
        data["temperature"] = temp
    return data


def stream_artefact_with_vision(
    project_description: str,
    date: str,
    user_bios: str,
    themes: str,
    location: str,
    selected_type: Dict[str, Any],
    images: List[dict],
    model_config: Dict[str, Any],
    closing_instruction: str,
    temperature: Optional[float] = None,
    retry_config: Optional[RetryConfig] = None
) -> Iterator[str]:
    """
    Vision-enhanced generation, yielding text chunks live.

    Works with Anthropic, or with an OpenRouter model whose config has
    ``supports_vision`` set. Suitable for ``st.write_stream``. On any failure
    an :class:`ErrorChunk` is yielded. Args mirror
    :func:`generate_artefact_with_vision`.
    """
    provider = model_config.get('provider', '')

    if provider not in ('anthropic', 'openrouter') or not model_config.get('supports_vision'):
        yield ErrorChunk(
            f"Error: Model '{model_config.get('model')}' ({provider}) cannot read images. "
            "Choose Anthropic, or a vision-capable OpenRouter model, in the sidebar."
        )
        return

    headers, error = auth_headers(model_config)
    if error:
        yield ErrorChunk(f"{error}. Please add it to your .env file.")
        return

    logging.info(f"Using {provider} vision ({model_config.get('model')}) with {len(images)} image(s)")

    # Build the dynamic text prompt (static instructions live in
    # VISION_SYSTEM_PROMPT; this carries only per-request project details).
    artefact_type = selected_type['category']

    text_prompt = f"""Project Information:
Description: {project_description}
Location: {location}
Date/Timeframe: {date}
User Personas: {user_bios}
Key Themes: {themes}

Artefact Category: {artefact_type}

Additional creative guidance: {closing_instruction}"""

    if provider == 'anthropic':
        data = prepare_vision_request_anthropic(text_prompt, images, model_config, temperature)
    else:
        data = prepare_vision_request_openrouter(text_prompt, images, model_config, temperature)

    logging.debug(f"Request contains {len(images)} images")

    # Stream the response (per-chunk timeout) so a long vision completion
    # doesn't trip a single large read timeout.
    yield from stream_response(model_config, headers, data, retry_config, timeout=120)
    logging.info("Completed vision-enhanced artifact stream")


def generate_artefact_with_vision(
    project_description: str,
    date: str,
    user_bios: str,
    themes: str,
    location: str,
    selected_type: Dict[str, Any],
    images: List[dict],
    model_config: Dict[str, Any],
    closing_instruction: str,
    temperature: Optional[float] = None,
    retry_config: Optional[RetryConfig] = None
) -> str:
    """Vision-enhanced generation returning the full text (or an error).

    Thin wrapper that exhausts :func:`stream_artefact_with_vision`; use that
    generator directly for live streaming.
    """
    return "".join(stream_artefact_with_vision(
        project_description, date, user_bios, themes, location,
        selected_type, images, model_config, closing_instruction,
        temperature=temperature, retry_config=retry_config
    ))
