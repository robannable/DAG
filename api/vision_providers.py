"""Vision-enhanced API provider functions"""
import os
import logging
from typing import Dict, Any, List, Optional
import requests
from api.retry import make_api_request_with_retry, RetryConfig


def prepare_vision_request_anthropic(
    text_prompt: str,
    images: List[dict],
    model_config: Dict[str, Any],
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """
    Prepare vision request for Anthropic Claude

    Args:
        text_prompt: Text prompt
        images: List of image data with base64 and media_type
        model_config: Model configuration
        temperature: Optional temperature override

    Returns:
        Request data dictionary
    """
    if temperature is not None:
        model_config = model_config.copy()
        model_config["temperature"] = temperature

    # Build system prompt
    system_prompt = """You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.

You have been provided with visual materials (sketches, diagrams, photographs, or reference images) along with text descriptions.

IMPORTANT: First, carefully analyze the provided images:
1. Spatial organization, layout, and relationships
2. Annotations, labels, or handwritten notes
3. Material indications and aesthetic qualities
4. Scale, proportion, and atmospheric intentions
5. Site context and environmental factors
6. Any diagrams or visual information systems

Then share your visual analysis within <think> tags before creating the final artifact."""

    # Build content array with images and text
    content = []

    # Add images first
    for idx, img in enumerate(images):
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img['media_type'],
                "data": img['base64']
            }
        })

    # Add text prompt
    content.append({
        "type": "text",
        "text": f"""Please analyze the {len(images)} image(s) I've shared above, then use that visual context along with this project description to create a diegetic artifact:

{text_prompt}

Remember to:
1. First explain your interpretation of the visual materials in <think> tags
2. Reference specific visual elements you observe
3. Then create the artifact that reflects both visual and textual context"""
    })

    return {
        "model": model_config["model"],
        "max_tokens": model_config["max_tokens"],
        "temperature": model_config["temperature"],
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }


def prepare_vision_request_openai(
    text_prompt: str,
    images: List[dict],
    model_config: Dict[str, Any],
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """
    Prepare vision request for OpenAI GPT-4 Vision

    Args:
        text_prompt: Text prompt
        images: List of image data with base64 and media_type
        model_config: Model configuration
        temperature: Optional temperature override

    Returns:
        Request data dictionary
    """
    if temperature is not None:
        model_config = model_config.copy()
        model_config["temperature"] = temperature

    # Build content array
    content = []

    # Add images
    for img in images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{img['media_type']};base64,{img['base64']}",
                "detail": "high"  # Use high detail for architectural images
            }
        })

    # Add text
    content.append({
        "type": "text",
        "text": f"""I'm sharing {len(images)} image(s) showing visual context for an architectural project.

Please analyze these images carefully, then use that visual interpretation along with the text description to create a diegetic artifact:

{text_prompt}

Structure your response:
<think>
Your analysis of the visual materials...
</think>

Then create the artifact reflecting both visual and textual context."""
    })

    return {
        "model": model_config["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are a dramatalurgical expert that creates diegetic artefacts for architectural projects. You analyze visual materials and combine them with text descriptions to create rich, contextual artifacts."
            },
            {
                "role": "user",
                "content": content
            }
        ],
        "max_tokens": model_config["max_tokens"],
        "temperature": model_config["temperature"]
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
    Generate artifact using vision-enhanced API

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

    # Check if provider supports vision
    if provider not in ['anthropic', 'openai']:
        return f"Error: Vision features not supported for provider '{provider}'. Please use Anthropic Claude or OpenAI GPT-4 Vision."

    # Get API key
    api_key = os.getenv(model_config['api_key_env'])
    if not api_key:
        return f"Error: {model_config['api_key_env']} not found in environment variables"

    # Prepare headers
    headers = model_config['headers'].copy()

    if provider == 'anthropic':
        headers["x-api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    # Log
    logging.info(f"Using vision-enhanced generation with {len(images)} image(s)")

    # Build the text prompt
    artefact_type = selected_type['category']

    text_prompt = f"""Project Information:
Description: {project_description}
Location: {location}
Date/Timeframe: {date}
User Personas: {user_bios}
Key Themes: {themes}

Artifact Category: {artefact_type}

Instructions:
1. Analyze the visual materials I've shared - what spatial, material, and contextual information do they convey?
2. Explain (100-150 words) your choice of specific artefact within the {artefact_type} category, informed by both visuals and text.
3. Summarize (2-3 sentences) how this artefact relates to the project's themes and visual context.
4. Pose 2-3 thought-provoking questions about the relationship between this artefact and the architecture project.
5. Create the diegetic artefact itself (500-750 words) using markdown. Reference specific elements from the visual materials. {closing_instruction}

The artifact should feel grounded in the actual visual context you've seen, not generic assumptions."""

    # Prepare request based on provider
    if provider == 'anthropic':
        data = prepare_vision_request_anthropic(
            text_prompt, images, model_config, temperature
        )
    else:  # openai
        data = prepare_vision_request_openai(
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
            error_message = f"API Error: {response.status_code} - {response.text}"
            logging.error(error_message)
            return error_message

        # Extract response
        response_json = response.json()

        if provider == 'anthropic':
            content = response_json['content'][0]['text']
        else:  # openai
            content = response_json['choices'][0]['message']['content']

        logging.info(f"Successfully generated vision-enhanced artifact ({len(content)} chars)")
        return content

    except Exception as e:
        error_message = f"Error generating vision-enhanced artefact: {str(e)}"
        logging.error(error_message)
        return error_message
