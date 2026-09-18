"""API provider classes and request handling"""
import os
import json
import logging
from typing import Dict, Any, Optional, Iterator, List, Tuple
import requests
from api.retry import (
    make_api_request_with_retry,
    make_streaming_request_with_retry,
    RetryConfig,
)

SUPPORTED_PROVIDERS = ("anthropic", "openrouter", "ollama")


class ErrorChunk(str):
    """A streamed chunk reporting a failure rather than artefact text.

    Behaves as a normal "Error:"-prefixed string (so it renders and joins
    like any chunk), but lets the caller tell a mid-stream failure apart
    from text that merely happens to start with "Error".
    """


def iter_anthropic_stream(response: requests.Response) -> Iterator[str]:
    """Yield text chunks from an Anthropic server-sent-events stream.

    Emits the text of each ``text_delta`` event as it arrives, so callers can
    render output live. On a streamed error event, yields a single
    :class:`ErrorChunk` and stops.
    """
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line or not raw_line.startswith("data:"):
            continue
        payload = raw_line[len("data:"):].strip()
        try:
            event = json.loads(payload)
        except (ValueError, json.JSONDecodeError):
            continue
        event_type = event.get("type")
        if event_type == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                yield delta.get("text", "")
        elif event_type == "message_delta":
            stop_reason = event.get("delta", {}).get("stop_reason")
            if stop_reason in ("max_tokens", "refusal"):
                logging.warning(f"Anthropic stream stopped early: {stop_reason}")
        elif event_type == "error":
            message = event.get("error", {}).get("message", "unknown streaming error")
            logging.error(f"Anthropic stream error: {message}")
            yield ErrorChunk(f"Error: API streaming error - {message}")
            return


def iter_openai_stream(response: requests.Response) -> Iterator[str]:
    """Yield text chunks from an OpenAI-style (OpenRouter) SSE stream.

    Skips SSE comments such as OpenRouter's ": OPENROUTER PROCESSING"
    keep-alive and stops at ``[DONE]``. OpenRouter reports failures after the
    200 status line as a chunk with a top-level ``error``; that yields a
    single :class:`ErrorChunk` and stops. Reasoning deltas are ignored.
    """
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line or not raw_line.startswith("data:"):
            continue
        payload = raw_line[len("data:"):].strip()
        if payload == "[DONE]":
            return
        try:
            chunk = json.loads(payload)
        except (ValueError, json.JSONDecodeError):
            continue
        if "error" in chunk:
            message = chunk["error"].get("message", "unknown streaming error")
            logging.error(f"OpenRouter stream error: {message}")
            yield ErrorChunk(f"Error: API streaming error - {message}")
            return
        for choice in chunk.get("choices", []):
            text = (choice.get("delta") or {}).get("content")
            if text:
                yield text
            if choice.get("finish_reason") == "length":
                logging.warning("OpenRouter stream stopped early: max_tokens reached")


def consume_anthropic_stream(response: requests.Response) -> str:
    """Accumulate an Anthropic stream into a single string.

    Thin wrapper over :func:`iter_anthropic_stream`; because text arrives
    continuously the read timeout (gap between chunks) never trips on a long
    completion. Returns the full text, or an "Error:"-prefixed string if the
    API streams an error event.
    """
    return "".join(iter_anthropic_stream(response))


# All static instruction scaffolding lives here so it forms a single,
# byte-identical prefix on every request. For Anthropic it is sent as a
# cache_control system block; the per-call user message carries only the
# dynamic project details. (Note: Anthropic only caches prefixes above a
# model-dependent minimum length, which this prompt is currently under, so
# caching is wired but dormant until the static prompt grows.)
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


def resolve_temperature(
    model_config: Dict[str, Any],
    temperature: Optional[float] = None
) -> Optional[float]:
    """The temperature to send, or None when the model rejects the parameter.

    Claude 5 models return a 400 if ``temperature`` is sent at all, so it is
    omitted whenever the config marks ``supports_temperature`` false.
    """
    if not model_config.get("supports_temperature", True):
        return None
    if temperature is not None:
        return temperature
    return model_config.get("temperature")


def auth_headers(model_config: Dict[str, Any]) -> Tuple[Dict[str, str], Optional[str]]:
    """Build request headers for a provider.

    Returns ``(headers, error)``; ``error`` is an "Error:" message when the
    provider is unsupported or its API key is missing.
    """
    provider = model_config.get('provider', '')
    headers = dict(model_config.get('headers', {}))

    if provider not in SUPPORTED_PROVIDERS:
        return headers, (
            f"Error: Unsupported provider {provider!r}. "
            f"Supported: {', '.join(SUPPORTED_PROVIDERS)}."
        )
    if provider == 'ollama':
        return headers, None

    api_key = os.getenv(model_config['api_key_env'])
    if not api_key:
        return headers, f"Error: {model_config['api_key_env']} not found in environment variables"
    if provider == 'anthropic':
        headers["x-api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers, None


def prepare_request_data(
    prompt: str,
    model_config: Dict[str, Any],
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """Wrap a fully-built user prompt in the provider's request shape.

    The static instructions live in SYSTEM_PROMPT; ``prompt`` is expected to
    contain only the dynamic, per-request content.
    """
    provider = model_config.get('provider', '')
    temp = resolve_temperature(model_config, temperature)

    if provider == 'anthropic':
        data = {
            "model": model_config["model"],
            "max_tokens": model_config["max_tokens"],
            "stream": True,
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
        if temp is not None:
            data["temperature"] = temp
        if model_config.get("thinking"):
            data["thinking"] = model_config["thinking"]
        return data

    if provider == 'openrouter':
        data = {
            "model": model_config["model"],
            "max_tokens": model_config["max_tokens"],
            "stream": True,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        }
        if temp is not None:
            data["temperature"] = temp
        return data

    if provider == 'ollama':
        options = {
            "top_p": model_config.get("top_p", 0.9),
            "num_predict": model_config["max_tokens"]
        }
        if temp is not None:
            options["temperature"] = temp
        return {
            "model": model_config["model"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": options
        }

    raise ValueError(
        f"Unsupported provider: {provider!r}. Supported: {', '.join(SUPPORTED_PROVIDERS)}."
    )


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


def stream_response(
    model_config: Dict[str, Any],
    headers: Dict[str, str],
    data: Dict[str, Any],
    retry_config: Optional[RetryConfig] = None,
    timeout: int = 60
) -> Iterator[str]:
    """POST a prepared request and yield text chunks for any provider.

    ``timeout`` is the maximum gap between streamed chunks. Non-200 statuses
    and exceptions yield a single :class:`ErrorChunk`.
    """
    provider = model_config.get('provider', '')
    logging.debug(f"Sending request to: {model_config['api_endpoint']}")
    logging.debug(f"Request data keys: {list(data.keys())}")

    try:
        if provider == 'ollama':
            # Ollama (local): non-streaming request is fine over localhost
            response = make_api_request_with_retry(
                model_config["api_endpoint"], headers, data,
                config=retry_config, timeout=timeout
            )
        else:
            # Stream so long completions don't hit the read timeout: tokens
            # arrive continuously instead of in one big read.
            response = make_streaming_request_with_retry(
                model_config["api_endpoint"], headers, data,
                config=retry_config, timeout=timeout
            )
        logging.debug(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            error_message = f"Error: API request failed (HTTP {response.status_code}) - {response.text}"
            logging.error(error_message)
            yield ErrorChunk(error_message)
            return

        if provider == 'anthropic':
            yield from iter_anthropic_stream(response)
        elif provider == 'openrouter':
            yield from iter_openai_stream(response)
        else:
            text = extract_response(response, model_config)
            yield ErrorChunk(text) if text.startswith("Error") else text
    except Exception as e:
        error_message = f"Error generating artefact: {str(e)}"
        logging.error(error_message)
        yield ErrorChunk(error_message)


def stream_artefact(
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
) -> Iterator[str]:
    """
    Generate a diegetic artefact, yielding text chunks as they arrive.

    Anthropic and OpenRouter responses stream token-by-token (suitable for
    ``st.write_stream``); for Ollama the full response is yielded as one
    chunk. On any failure an :class:`ErrorChunk` is yielded.

    Args mirror :func:`generate_artefact`.
    """
    headers, error = auth_headers(model_config)
    if error:
        yield ErrorChunk(error)
        return

    logging.info(f"Using provider: {model_config.get('provider')} ({model_config.get('model')})")

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

    data = prepare_request_data(prompt, model_config, temperature)
    yield from stream_response(model_config, headers, data, retry_config, timeout=60)


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
    """Generate a diegetic artefact and return the full text (or an error).

    Thin wrapper that exhausts :func:`stream_artefact`; use that generator
    directly for live streaming.
    """
    return "".join(stream_artefact(
        project_description, date, user_bios, themes, location,
        selected_type, model_config, closing_instruction,
        temperature=temperature, retry_config=retry_config
    ))


def _per_million(price: Any) -> Optional[float]:
    """OpenRouter quotes USD per token as a string; convert to per 1M tokens."""
    try:
        value = float(price)
    except (TypeError, ValueError):
        return None
    return value * 1_000_000 if value >= 0 else None


def parse_openrouter_models(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reduce OpenRouter's /models payload to what the model picker needs.

    Keeps text-output models, drops ``:batch`` variants (asynchronous, no
    streaming), and records whether each model accepts ``temperature`` and
    image input. Sorted by display name.
    """
    models = []
    for m in payload.get("data", []):
        model_id = m.get("id", "")
        arch = m.get("architecture") or {}
        if not model_id or model_id.endswith(":batch"):
            continue
        if "text" not in arch.get("output_modalities", ["text"]):
            continue
        pricing = m.get("pricing") or {}
        models.append({
            "id": model_id,
            "name": m.get("name") or model_id,
            "supports_temperature": "temperature" in (m.get("supported_parameters") or []),
            "supports_vision": "image" in arch.get("input_modalities", []),
            "prompt_price": _per_million(pricing.get("prompt")),
            "completion_price": _per_million(pricing.get("completion")),
        })
    models.sort(key=lambda x: x["name"].lower())
    return models


def get_openrouter_models(models_endpoint: str) -> List[Dict[str, Any]]:
    """Fetch the public OpenRouter model list (no API key needed).

    Returns an empty list on any failure so the UI can fall back to a
    free-text model field.
    """
    try:
        response = requests.get(models_endpoint, timeout=15)
        response.raise_for_status()
        return parse_openrouter_models(response.json())
    except Exception as e:
        logging.error(f"Error fetching OpenRouter models: {str(e)}")
        return []


def get_available_ollama_models() -> list:
    """Get list of available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        return []
    except Exception as e:
        logging.error(f"Error fetching Ollama models: {str(e)}")
        return []
