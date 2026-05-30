"""Vision-enhanced API provider functions - Anthropic Claude only"""
import os
import logging
from typing import Dict, Any, List, Optional, Iterator
import requests
from api.retry import make_streaming_request_with_retry, RetryConfig
from api.providers import iter_anthropic_stream


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
    if temperature is not None:
        model_config = model_config.copy()
        model_config["temperature"] = temperature

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

    content.append({
        "type": "text",
        "text": f"Please analyze the {len(images)} image(s) shared above and use that "
                f"visual context together with the project details below.\n\n{text_prompt}"
    })

    return {
        "model": model_config["model"],
        "max_tokens": model_config["max_tokens"],
        "temperature": model_config["temperature"],
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
    Vision-enhanced generation (Anthropic only), yielding text chunks live.

    Suitable for ``st.write_stream``. On any failure a single
    "Error:"-prefixed chunk is yielded. Args mirror
    :func:`generate_artefact_with_vision`.
    """
    provider = model_config.get('provider', '')

    # Check if provider supports vision (Anthropic only)
    if provider != 'anthropic':
        yield f"Error: Vision features only supported with Anthropic Claude. Current provider: '{provider}'. Please switch to Anthropic in the sidebar."
        return

    # Get API key
    api_key = os.getenv(model_config['api_key_env'])
    if not api_key:
        yield f"Error: {model_config['api_key_env']} not found in environment variables. Please add it to your .env file."
        return

    # Prepare headers (Anthropic format)
    headers = model_config['headers'].copy()
    headers["x-api-key"] = api_key

    # Log
    logging.info(f"Using Anthropic Claude vision with {len(images)} image(s)")

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

    # Prepare request for Anthropic
    data = prepare_vision_request_anthropic(
        text_prompt, images, model_config, temperature
    )

    # Log request
    logging.debug(f"Sending vision request to: {model_config['api_endpoint']}")
    logging.debug(f"Request contains {len(images)} images")

    try:
        # Stream the response (per-chunk timeout) so a long vision completion
        # doesn't trip a single large read timeout.
        response = make_streaming_request_with_retry(
            model_config["api_endpoint"],
            headers,
            data,
            config=retry_config,
            timeout=120  # max gap between chunks
        )

        logging.debug(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            error_message = f"Error: API request failed (HTTP {response.status_code}) - {response.text}"
            logging.error(error_message)
            yield error_message
            return

        yield from iter_anthropic_stream(response)
        logging.info("Completed vision-enhanced artifact stream")

    except Exception as e:
        error_message = f"Error generating vision-enhanced artefact: {str(e)}"
        logging.error(error_message)
        yield error_message


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
