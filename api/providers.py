"""API provider classes and request handling"""
import os
import logging
from typing import Dict, Any, Optional
import requests
from api.retry import make_api_request_with_retry, RetryConfig


# All static instruction scaffolding lives here so it forms a single,
# byte-identical prefix on every request. For Anthropic it is sent as a
# cache_control system block; the per-call user message carries only the
# dynamic project details. (Note: Anthropic only caches prefixes of >=1024
# tokens, which this prompt is currently under, so caching is wired but
# dormant until the static prompt grows past that threshold.)
SYSTEM_PROMPT = """You are a dramaturgical expert that creates diegetic artefacts for architectural projects.

Your task is to imagine and create a specific diegetic artefact within a given category that exists within the narrative world of a project. First, decide on an appropriate specific artefact type within that category that would be meaningful for the project.

Structure every response in this order:

1. First, share your reasoning within <think> tags, like this:
<think>
Here I analyze what would be most effective for this project...
</think>
The <think> section will not be visible to the end user unless they choose to see it.

2. Briefly explain (100-150 words) your choice of specific artefact within the given category.
3. Add a brief summary (2-3 sentences) of how this artefact relates to the project's themes and context.
4. Pose 2-3 thought-provoking questions for the user about the relationship between this artefact and the architecture project.
5. Finally, create the diegetic artefact itself (500-750 words) in an appropriate format and style, using markdown so it is visibly distinct.

Markdown formatting guidelines:
- Use proper heading hierarchy (# for main title, ## for sections, ### for subsections)
- Format emphasis appropriately (* for italic, ** for bold)
- Use proper list formatting (- for unordered lists, 1. for ordered lists)
- Include line breaks between paragraphs for readability
- Use horizontal rules (---) to separate major sections

Put the most important parts first and conclude with a proper ending so the artefact is complete and never cut off."""


def prepare_request_data(
    prompt: str,
    model_config: Dict[str, Any],
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """Wrap a fully-built user prompt in the provider's request shape.

    The static instructions live in SYSTEM_PROMPT; ``prompt`` is expected to
    contain only the dynamic, per-request content.
    """
    if temperature is not None:
        model_config = model_config.copy()
        model_config["temperature"] = temperature

    provider = model_config.get('provider', '')

    if provider == 'anthropic':
        return {
            "model": model_config["model"],
            "max_tokens": model_config["max_tokens"],
            "temperature": model_config["temperature"],
            "system": [
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

    if provider == 'ollama':
        return {
            "model": model_config["model"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": model_config["temperature"],
                "top_p": model_config.get("top_p", 0.9),
                "num_predict": model_config["max_tokens"]
            }
        }

    raise ValueError(f"Unsupported provider: {provider!r}. Supported: anthropic, ollama.")


def extract_response(response: requests.Response, model_config: Dict[str, Any]) -> str:
    """Extract the response content based on the provider's response format"""
    provider = model_config.get('provider', '')

    response_json = response.json()
    logging.debug(f"Response keys: {list(response_json.keys())}")

    if provider == 'anthropic':
        try:
            return response_json['content'][0]['text']
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting Anthropic response: {str(e)}")
            logging.debug(f"Response content: {response_json}")
            return f"Error parsing response: {str(e)}"

    if provider == 'ollama':
        try:
            return response_json['message']['content']
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting response: {str(e)}")
            logging.debug(f"Response content: {response_json}")
            return f"Error parsing response: {str(e)}"


def generate_artefact(
    project_description: str,
    date: str,
    user_bios: str,
    themes: str,
    location: str,
    selected_type: Dict[str, Any],
    model_config: Dict[str, Any],
    closing_instruction: str,
    temperature: Optional[float] = None,
    retry_config: Optional[RetryConfig] = None
) -> str:
    """
    Generate a diegetic artefact using the configured API provider

    Args:
        project_description: Description of the project
        date: Date or timeframe
        user_bios: User personas
        themes: Key themes
        location: Project location
        selected_type: Selected artefact type
        model_config: Model configuration
        closing_instruction: Closing instruction from config
        temperature: Optional temperature override
        retry_config: Optional retry configuration

    Returns:
        Generated artefact content or error message
    """
    provider = model_config.get('provider', '')
    headers = model_config['headers'].copy()

    if provider == 'anthropic':
        api_key = os.getenv(model_config['api_key_env'])
        if not api_key:
            return f"Error: {model_config['api_key_env']} not found in environment variables"
        headers["x-api-key"] = api_key
    elif provider != 'ollama':
        return f"Error: Unsupported provider {provider!r}. Supported: anthropic, ollama."

    logging.info(f"Using provider: {provider}")

    # Get the selected artefact type
    artefact_type = selected_type['category']

    # Build the dynamic, per-request prompt. All static instructions live in
    # SYSTEM_PROMPT, so this carries only project details and the budget.
    safe_tokens = int(model_config["max_tokens"] * 0.9)
    prompt = f"""Project Information:
Description: {project_description}
Location: {location}
Date/Timeframe: {date}
User Personas: {user_bios}
Key Themes: {themes}

Artefact Category: {artefact_type}

Additional creative guidance: {closing_instruction}

Keep your entire response within approximately {safe_tokens} tokens, and make sure the artefact is complete and not cut off."""

    # Prepare request data based on provider
    data = prepare_request_data(prompt, model_config, temperature)

    # Log request information (without sensitive data)
    logging.debug(f"Sending request to: {model_config['api_endpoint']}")
    logging.debug(f"Request data keys: {list(data.keys())}")

    try:
        # Make API request with retry logic
        response = make_api_request_with_retry(
            model_config["api_endpoint"],
            headers,
            data,
            config=retry_config,
            timeout=60
        )

        # Log response information
        logging.debug(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            error_message = f"API Error: {response.status_code} - {response.text}"
            logging.error(error_message)
            return error_message

        response_content = extract_response(response, model_config)
        response_length = len(response_content)
        if response_length > (model_config["max_tokens"] * 0.9):
            logging.warning(f"Response approaching token limit: {response_length} tokens")
        return response_content
    except Exception as e:
        error_message = f"Error generating artefact: {str(e)}"
        logging.error(error_message)
        return error_message


def get_available_ollama_models() -> list:
    """Get list of available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        return []
    except Exception as e:
        logging.error(f"Error fetching Ollama models: {str(e)}")
        return []
