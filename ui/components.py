"""UI components for DAG application"""
import streamlit as st
from utils.config import load_model_config


def get_model_temperature() -> float:
    """Render temperature slider and return selected value"""
    model_config = load_model_config()
    provider = model_config.get('provider', '')
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


def render_sidebar(config: dict, provider_options: dict):
    """Render the sidebar with model settings"""
    st.header("Model Settings")

    def on_model_change():
        new_provider = provider_options[st.session_state.model_selector]
        st.session_state.current_provider = new_provider
        # Update config file
        from utils.config import save_model_config
        save_model_config(new_provider)

    # Model provider selection with formatted display
    current_display = next(
        display for display, provider in provider_options.items()
        if provider == st.session_state.current_provider
    )

    selected_display = st.selectbox(
        "Choose Model Provider",
        options=list(provider_options.keys()),
        index=list(provider_options.keys()).index(current_display),
        key='model_selector',
        on_change=on_model_change
    )

    # Show Ollama model input if needed
    if st.session_state.current_provider == 'ollama':
        from api.providers import get_available_ollama_models
        from utils.config import update_ollama_model

        available_models = get_available_ollama_models()
        if not available_models:
            st.warning("No Ollama models found. Please make sure Ollama is running and you have pulled at least one model.")
            ollama_model = st.text_input(
                "Ollama Model Name",
                value=config['providers']['ollama'].get('model', 'cogito'),
                help="Enter the name of your locally installed Ollama model"
            )
        else:
            ollama_model = st.selectbox(
                "Select Ollama Model",
                options=available_models,
                index=available_models.index(config['providers']['ollama'].get('model', 'cogito')) if config['providers']['ollama'].get('model', 'cogito') in available_models else 0,
                help="Select from your locally installed Ollama models"
            )

        update_ollama_model(ollama_model)
        st.caption("Make sure you have pulled your chosen model using 'ollama pull model_name'")

    # Temperature slider
    temperature = get_model_temperature()

    # Add spacer to push description to bottom
    st.markdown("<br>" * 5, unsafe_allow_html=True)

    # Add separator and description at the very bottom
    st.markdown("---")
    st.caption("""
    This tool generates speculative documents and artefacts for architectural projects, helping explore social, cultural, and practical implications of spatial interventions.

    [![GitHub](https://img.shields.io/badge/GitHub-View_Source-blue?logo=GitHub)](https://github.com/robannable/DAG)
    """)

    return temperature
