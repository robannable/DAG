"""API provider classes and request handling"""
import os
import logging
from typing import Dict, Any, Optional
import requests
from api.retry import make_api_request_with_retry, RetryConfig


def calculate_max_tokens(project_description: str, user_bios: str, themes: str) -> int:
    """Calculate appropriate max tokens based on input complexity"""
    input_length = len(project_description) + len(user_bios) + len(themes)

    if input_length > 1000:
        # Complex project needs more concise output
        return 1400
    else:
        # Simpler project can have slightly more detailed output
        return 1600


def prepare_request_data(
    prompt: str,
    model_config: Dict[str, Any],
    project_description: str,
    user_bios: str,
    themes: str,
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """Prepare the request data based on the provider's requirements"""
    if temperature is not None:
        model_config = model_config.copy()
        model_config["temperature"] = temperature

    provider = model_config.get('provider', '')

    # Calculate buffer tokens for completion
    response_tokens = model_config["max_tokens"]
    safe_tokens = int(response_tokens * 0.9)  # Use 90% of max_tokens as safe limit

    # Add token guidance to prompt
    enhanced_prompt = prompt + f"\n\nYour response should be complete and no longer than approximately {safe_tokens} tokens."

    if provider == 'anthropic':
        # Custom system prompt for Anthropic that requests thinking in <think> tags
        system_prompt = """You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.

        IMPORTANT: In your response, first share your reasoning process within <think> tags. Use this format:
        <think>
        Here I analyze what would be most effective for this project...
        </think>

        Then provide your final output after the thinking section. The <think> section won't be visible to the end user unless they choose to see it."""

        return {
            "model": model_config["model"],
            "max_tokens": model_config["max_tokens"],
            "temperature": model_config["temperature"],
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": enhanced_prompt + "\n\nIMPORTANT: First explain your reasoning within <think> tags before creating the final artifact. This thinking will help me understand your creative process."
                }
            ]
        }
    elif provider == 'ollama':
        # Ollama uses a simpler format with a system prompt and messages
        system_prompt = """You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.

        IMPORTANT: In your response, first share your reasoning process within <think> tags. Use this format:
        <think>
        Here I analyze what would be most effective for this project...
        </think>

        Then provide your final output after the thinking section. The <think> section won't be visible to the end user unless they choose to see it."""

        return {
            "model": model_config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": enhanced_prompt + "\n\nFirst explain your reasoning within <think> tags before creating the final artifact."
                }
            ],
            "stream": False,
            "options": {
                "temperature": model_config["temperature"],
                "top_p": model_config.get("top_p", 0.9),
                "num_predict": model_config["max_tokens"]
            }
        }
    else:  # Default to OpenAI/Perplexity format
        data = {
            "model": model_config["model"],
            "messages": [{
                "role": "system",
                "content": """You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.

                IMPORTANT: Structure your response in exactly two parts:
                1. First, a thinking section wrapped in <think> tags that explains your reasoning
                2. Then, the final artifact output after a clear closing </think> tag

                Example structure:
                <think>
                Your reasoning here...
                </think>

                Your final artifact here..."""
            },
            {
                "role": "user",
                "content": enhanced_prompt + "\n\nIMPORTANT: Begin with your reasoning in <think> tags, then close the tag with </think> before providing the final artifact."
            }],
            "max_tokens": calculate_max_tokens(project_description, user_bios, themes),
            "temperature": model_config["temperature"],
            "top_p": model_config.get("top_p", 0.9),
            "presence_penalty": model_config.get("presence_penalty", 0.1)
        }

        return data


def extract_response(response: requests.Response, model_config: Dict[str, Any]) -> str:
    """Extract the response content based on the provider's response format"""
    provider = model_config.get('provider', '')

    # Log the response structure to help with debugging
    response_json = response.json()
    logging.debug(f"Response keys: {list(response_json.keys())}")

    if provider == 'anthropic':
        # Anthropic response structure
        try:
            return response_json['content'][0]['text']
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting Anthropic response: {str(e)}")
            logging.debug(f"Response content: {response_json}")
            return f"Error parsing response: {str(e)}"
    elif provider == 'ollama':
        # Ollama response structure
        try:
            return response_json['message']['content']
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting Ollama response: {str(e)}")
            logging.debug(f"Response content: {response_json}")
            return f"Error parsing response: {str(e)}"
    else:  # Default to OpenAI/Perplexity format
        try:
            return response_json['choices'][0]['message']['content']
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
    # Get API key if required
    provider = model_config.get('provider', '')
    api_key = None
    if provider != 'ollama':  # Ollama doesn't require an API key
        api_key = os.getenv(model_config['api_key_env'])
        if not api_key:
            return f"Error: {model_config['api_key_env']} not found in environment variables"

    # Prepare headers
    headers = model_config['headers'].copy()

    # Handle provider-specific authorization formats
    if provider == 'anthropic':
        # Anthropic uses x-api-key instead of Authorization: Bearer
        headers["x-api-key"] = api_key
    elif provider != 'ollama':  # Ollama doesn't require authorization
        # Default Bearer format for other providers
        headers["Authorization"] = f"Bearer {api_key}"

    # Log which provider we're using
    logging.info(f"Using provider: {provider if provider else 'default'}")

    # Get the selected artefact type
    artefact_type = selected_type['category']

    # Build the prompt
    prompt = f"""You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.
    Your task is to imagine and create a specific diegetic artefact within the category of '{artefact_type}' that exists within the narrative world of this project.
    First, decide on an appropriate specific artefact type within this category that would be meaningful for this project.

    Project Information:
    Description: {project_description}
    Location: {location}
    Date/Timeframe: {date}
    User Personas: {user_bios}
    Key Themes: {themes}

    Instructions:
    1. Begin by briefly explaining (100-150 words) your choice of specific artefact within the {artefact_type} category.
    2. Add a brief summary (2-3 sentences) explaining how this artefact relates to the project's themes and context.
    3. Pose 2-3 thought-provoking questions for the user to consider about the relationship between this artefact and the architecture project.
    4. Finally, create the diegetic artefact itself (500-750 words) in the appropriate format and style using markdown syntax to ensure it is visibly distinct. Refer to {closing_instruction} for additional abductive thinking opportunities. Ensure content is not truncated by the target word count and token limit. Rewrite to avoid this if necessary.

    Markdown Formatting Guidelines:
    - Use proper heading hierarchy (# for main title, ## for sections, ### for subsections)
    - Format emphasis appropriately (* for italic, ** for bold)
    - Use proper list formatting (- for unordered lists, 1. for ordered lists)
    - Include line breaks between paragraphs for readability
    - Use horizontal rules (---) to separate major sections

    IMPORTANT: Your entire response must fit within {model_config["max_tokens"]} tokens.
    Structure your response to ensure your artefact is complete and not cut off.
    The most important parts should come first, and conclude with a proper ending.

    Begin your response:"""

    # Prepare request data based on provider
    data = prepare_request_data(
        prompt, model_config, project_description, user_bios, themes, temperature
    )

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
