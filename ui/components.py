"""UI components for DAG application"""
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from utils.config import load_model_config, enabled_providers
from api.providers import get_openrouter_models, get_available_ollama_models

PROVIDER_LABELS = {
    "anthropic": "Anthropic",
    "openrouter": "OpenRouter (many models)",
    "ollama": "Ollama (local)",
}


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_openrouter_models(models_endpoint: str) -> List[Dict[str, Any]]:
    return get_openrouter_models(models_endpoint)


def _format_price(model: Dict[str, Any]) -> str:
    prompt, completion = model["prompt_price"], model["completion_price"]
    if prompt is None or completion is None:
        return "variable price"
    if prompt == 0 and completion == 0:
        return "free"
    return f"${prompt:.2f} / ${completion:.2f} per M tokens"


def get_model_temperature(model_config: Dict[str, Any]) -> Optional[float]:
    """Render the temperature slider, or return None if the model rejects it"""
    if not model_config.get("supports_temperature", True):
        st.caption(
            f"`{model_config.get('model')}` sets its own sampling; "
            "temperature isn't adjustable for this model."
        )
        return None

    default_temp = model_config.get("temperature", 0.7)

    # Get temperature range from config
    temp_range = model_config.get("temperature_range", {
        "min": 0.0,
        "max": 1.0,
        "step": 0.1
    })

    # Validate temperature range
    min_temp = float(temp_range.get("min", 0.0))
    max_temp = float(temp_range.get("max", 1.0))
    step = float(temp_range.get("step", 0.1))

    # Ensure valid range
    if min_temp >= max_temp:
        min_temp, max_temp = 0.0, 1.0

    # Ensure default temperature is within valid range
    default_temp = min(max(default_temp, min_temp), max_temp)

    temp_value = st.slider(
        "Model Temperature",
        min_value=min_temp,
        max_value=max_temp,
        value=default_temp,
        step=step,
        label_visibility="visible",
        help=f"Technical: Temperature controls the randomness in the model's token selection process. Lower values increase the probability of selecting the most likely next token, while higher values make the distribution more uniform across all possible tokens. Range: {min_temp} to {max_temp}"
    )

    st.caption("Lower values (0) create focused outputs, higher values create more creative, varied outputs")

    return temp_value


def _select_openrouter_model(model_config: Dict[str, Any]) -> Dict[str, Any]:
    """Model picker for OpenRouter; returns the config with the choice applied"""
    models = _cached_openrouter_models(model_config["models_endpoint"])
    default_id = model_config["model"]

    if not models:
        st.warning("Couldn't load the OpenRouter model list. Enter a model ID instead.")
        model_config["model"] = st.text_input(
            "OpenRouter Model ID",
            value=default_id,
            key="openrouter_model_text",
            help="e.g. google/gemini-3.8-flash - see openrouter.ai/models"
        )
        # Capabilities unknown: send temperature, don't offer vision
        model_config["supports_vision"] = False
        return model_config

    by_id = {m["id"]: m for m in models}
    ids = list(by_id)
    selected = st.selectbox(
        "OpenRouter Model",
        options=ids,
        index=ids.index(default_id) if default_id in by_id else 0,
        format_func=lambda i: by_id[i]["name"],
        key="openrouter_model",
        help="Type to search. Prices are per million input / output tokens."
    )
    chosen = by_id[selected]
    st.caption(
        f"`{selected}` · {_format_price(chosen)}"
        + (" · reads images" if chosen["supports_vision"] else "")
    )
    model_config["model"] = selected
    model_config["supports_temperature"] = chosen["supports_temperature"]
    model_config["supports_vision"] = chosen["supports_vision"]
    return model_config


def _select_ollama_model(model_config: Dict[str, Any]) -> Dict[str, Any]:
    available_models = get_available_ollama_models()
    default_model = model_config.get('model', 'cogito')
    if not available_models:
        st.warning("No Ollama models found. Please make sure Ollama is running and you have pulled at least one model.")
        model_config["model"] = st.text_input(
            "Ollama Model Name",
            value=default_model,
            key="ollama_model_text",
            help="Enter the name of your locally installed Ollama model"
        )
    else:
        model_config["model"] = st.selectbox(
            "Select Ollama Model",
            options=available_models,
            index=available_models.index(default_model) if default_model in available_models else 0,
            key="ollama_model",
            help="Select from your locally installed Ollama models"
        )
    st.caption("Make sure you have pulled your chosen model using 'ollama pull model_name'")
    return model_config


def render_sidebar(config: dict) -> Tuple[Dict[str, Any], Optional[float]]:
    """Render model settings; return (active model config, temperature).

    All choices are kept in this browser session only - nothing is written
    back to model_config.json, so users on a shared server don't change
    each other's settings.
    """
    st.header("Model Settings")

    providers = enabled_providers(config)
    if st.session_state.get('current_provider') not in providers:
        default = config.get('current_provider', 'anthropic')
        st.session_state.current_provider = default if default in providers else providers[0]

    provider = st.selectbox(
        "Choose Model Provider",
        options=providers,
        index=providers.index(st.session_state.current_provider),
        format_func=lambda p: PROVIDER_LABELS.get(p, p.title()),
        key='model_selector',
    )
    st.session_state.current_provider = provider

    model_config = load_model_config(provider)
    if provider == 'openrouter':
        model_config = _select_openrouter_model(model_config)
    elif provider == 'ollama':
        model_config = _select_ollama_model(model_config)
    else:
        st.caption(f"Model: `{model_config.get('model')}`")

    temperature = get_model_temperature(model_config)

    # Add spacer to push description to bottom
    st.markdown("<br>" * 5, unsafe_allow_html=True)

    # Add separator and description at the very bottom
    st.markdown("---")
    st.caption("""
    This tool generates speculative documents and artefacts for architectural projects, helping explore social, cultural, and practical implications of spatial interventions.

    [![GitHub](https://img.shields.io/badge/GitHub-View_Source-blue?logo=GitHub)](https://github.com/robannable/DAG)
    """)

    return model_config, temperature
