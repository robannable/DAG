"""Vision-enhanced API provider functions - Anthropic Claude only"""
import os
import logging
from typing import Dict, Any, List, Optional
import requests
from api.retry import make_api_request_with_retry, RetryConfig


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
    """
    Generate artifact using vision-enhanced API (Anthropic Claude only)

    Args:
        project_description: Project description
        date: Date/timeframe
        user_bios: User personas
        themes: Key themes
        location: Location
        selected_type: Selected artifact type
        images: List of processed image data
        model_config: Model configuration
        closing_instruction: Closing instruction
        temperature: Optional temperature
        retry_config: Optional retry config

    Returns:
        Generated artifact content or error message
    """
    provider = model_config.get('provider', '')

    # Check if provider supports vision (Anthropic only)
    if provider != 'anthropic':
        return f"Error: Vision features only supported with Anthropic Claude. Current provider: '{provider}'. Please switch to Anthropic in the sidebar."

    # Get API key
    api_key = os.getenv(model_config['api_key_env'])
    if not api_key:
        return f"Error: {model_config['api_key_env']} not found in environment variables. Please add it to your .env file."

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
        # Make request with retry
        response = make_api_request_with_retry(
            model_config["api_endpoint"],
            headers,
            data,
            config=retry_config,
            timeout=120  # Longer timeout for vision
        )

        logging.debug(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            error_message = f"Error: API request failed (HTTP {response.status_code}) - {response.text}"
            logging.error(error_message)
            return error_message

        # Extract response (Anthropic format)
        response_json = response.json()
        content = response_json['content'][0]['text']

        logging.info(f"Successfully generated vision-enhanced artifact ({len(content)} chars)")
        return content

    except Exception as e:
        error_message = f"Error generating vision-enhanced artefact: {str(e)}"
        logging.error(error_message)
        return error_message
