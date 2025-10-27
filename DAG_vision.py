"""
Diegetic Artefact Generator (DAG) - Vision Enhanced
Multimodal version supporting image inputs with AI vision interpretation
"""
import streamlit as st

# Configure the page - this must be the first st command
st.set_page_config(
    page_title="DAG - Vision Enhanced",
    page_icon="🎭",
    layout="wide"
)

import os
import json
import pathlib
from dotenv import load_dotenv

# Import custom modules
from utils.logging_config import setup_logging
from utils.config import (
    load_artefact_categories,
    load_prompt_instructions,
    load_model_config
)
from utils.file_operations import save_artefact
from utils.image_processing import prepare_images_for_api
from api.providers import generate_artefact
from api.vision_providers import generate_artefact_with_vision
from api.retry import RetryConfig
from ui.components import render_sidebar
from ui.gallery import render_gallery, display_artifact
from ui.image_upload import (
    render_image_upload_section,
    display_image_previews,
    display_vision_interpretation,
    render_vision_status_messages,
    extract_think_content
)

# Set up logging
setup_logging()

# Load environment variables
load_dotenv()


# Load CSS
def load_css():
    """Load CSS stylesheets"""
    # Load main styles
    css_file = pathlib.Path(__file__).parent / "static" / "styles.css"
    with open(css_file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    # Load generated content styles
    generated_css_file = pathlib.Path(__file__).parent / "static" / "generated_content.css"
    with open(generated_css_file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


load_css()

# Initialize session state
if 'artefacts' not in st.session_state:
    st.session_state.artefacts = []
if 'show_thinking' not in st.session_state:
    st.session_state.show_thinking = False
if 'current_provider' not in st.session_state:
    st.session_state.current_provider = 'anthropic'
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'show_gallery' not in st.session_state:
    st.session_state.show_gallery = False
if 'viewing_artifact' not in st.session_state:
    st.session_state.viewing_artifact = None

# Main interface
st.title("🎭 Diegetic Artefact Generator")
st.markdown("### Vision Enhanced - Now with Image Analysis")
st.markdown("""
Generate speculative documents and artefacts for architectural projects.
**New:** Upload sketches, diagrams, or photos for AI-powered visual analysis.
""")

# Sidebar controls
with st.sidebar:
    # Load model configurations
    with open('model_config.json', 'r') as f:
        config = json.load(f)

    # Create formatted options for the dropdown
    provider_options = {
        f"{provider.title()} ({config['providers'][provider]['model']})": provider
        for provider in config['providers'].keys()
    }

    # Render sidebar and get temperature
    temperature = render_sidebar(config, provider_options)

# Add tab navigation
tab1, tab2 = st.tabs(["Generate", "Gallery"])

with tab1:
    # Image upload section (outside form for better UX)
    uploaded_files, use_vision = render_image_upload_section()

    # Show image previews if uploaded
    if uploaded_files:
        display_image_previews(uploaded_files)

    # Input form
    with st.form("artefact_form"):
        col1, col2 = st.columns(2)

        with col1:
            project_description = st.text_area(
                "Project Description",
                placeholder="Project name and brief description?...",
                height=100
            )
            location = st.text_input(
                "Project Location",
                placeholder="e.g., Birmingham, UK or specific address"
            )
            date = st.text_input(
                "Date/Timeframe",
                placeholder="e.g., 2025, 2030, or 'Alternative Present'"
            )
            # Move category selection here, under the date
            artefact_types = load_artefact_categories()
            selected_category = st.selectbox(
                "Choose Artefact Category",
                options=artefact_types,
                help="Select the category of diegetic artefact you want to generate"
            )

        with col2:
            user_bios = st.text_area(
                "User Personas",
                placeholder="Describe the key users or inhabitants of the space...include names and personalities if you wish.",
                height=150
            )
            themes = st.text_area(
                "Key Themes",
                placeholder="List the main themes, socioeconomic contexts, and political frameworks...",
                height=160
            )

        # Center and style the generate button
        st.markdown("<div style='padding: 10px 0px;'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "Generate Artefact" if not (uploaded_files and use_vision) else "Generate with Vision 🔍",
                use_container_width=True,
                type="primary"
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Generate and display results
    if submitted:
        if not all([project_description, date, user_bios, themes, location, selected_category]):
            st.warning("Please fill in all fields before generating an artefact.")
        else:
            # Load model config
            model_config = load_model_config()

            # Check if using vision
            if uploaded_files and use_vision:
                # Check if provider supports vision
                can_use_vision = render_vision_status_messages(
                    uploaded_files, use_vision, model_config
                )

                if not can_use_vision:
                    st.stop()

                # Process images
                with st.spinner("Processing images..."):
                    processed_images = prepare_images_for_api(
                        uploaded_files,
                        resize=True,
                        max_images=5
                    )

                if not processed_images:
                    st.error("No valid images could be processed. Please check your image files.")
                    st.stop()

                # Generate with vision
                with st.spinner(f"Analyzing {len(processed_images)} image(s) and generating artifact..."):
                    selected_type = {"category": selected_category, "items": [selected_category]}
                    closing_instruction = load_prompt_instructions()

                    retry_config = RetryConfig(
                        max_retries=3,
                        base_delay=1.0,
                        max_delay=10.0
                    )

                    st.session_state.current_artefact = generate_artefact_with_vision(
                        project_description,
                        date,
                        user_bios,
                        themes,
                        location,
                        selected_type,
                        processed_images,
                        model_config,
                        closing_instruction,
                        temperature=temperature,
                        retry_config=retry_config
                    )

            else:
                # Standard text-only generation
                with st.spinner("Generating your diegetic artefact..."):
                    selected_type = {"category": selected_category, "items": [selected_category]}
                    closing_instruction = load_prompt_instructions()

                    retry_config = RetryConfig(
                        max_retries=3,
                        base_delay=1.0,
                        max_delay=10.0
                    )

                    st.session_state.current_artefact = generate_artefact(
                        project_description,
                        date,
                        user_bios,
                        themes,
                        location,
                        selected_type,
                        model_config,
                        closing_instruction,
                        temperature=temperature,
                        retry_config=retry_config
                    )

            if not st.session_state.current_artefact.startswith("Error"):
                # Extract thinking content if present
                artifact_content, think_content = extract_think_content(
                    st.session_state.current_artefact
                )

                # Save the artefact to a file
                filename = save_artefact(
                    st.session_state.current_artefact,
                    project_description,
                    date,
                    location,
                    user_bios,
                    themes,
                    model_config,
                    temperature,
                    st.session_state.show_thinking
                )
                st.session_state.current_filename = filename

                # Show vision interpretation if available
                if think_content and uploaded_files and use_vision:
                    display_vision_interpretation(think_content)

                st.success(f"✅ Artefact saved to: {filename}")

    # Display section (outside the form and submit block)
    if 'current_artefact' in st.session_state and not st.session_state.current_artefact.startswith("Error"):
        show_thinking = st.checkbox("Show AI thinking process", value=st.session_state.show_thinking)
        st.session_state.show_thinking = show_thinking

        # Process the artefact content to handle think blocks
        content_parts = []
        for line in st.session_state.current_artefact.split('\n'):
            if '<think>' in line:
                content_parts.append('<div class="think-block">')
            elif '</think>' in line:
                content_parts.append('</div>')
            else:
                content_parts.append(line)

        # Combine the content and wrap it in a container with generated-content class
        container_classes = ["generated-content"]
        if show_thinking:
            container_classes.append("show-think")

        content = '\n'.join(content_parts)
        st.markdown(
            f'<div class="{" ".join(container_classes)}">{content}</div>',
            unsafe_allow_html=True
        )

        # Add a download button
        st.download_button(
            label="Download Artefact",
            data=st.session_state.current_artefact,
            file_name=os.path.basename(st.session_state.current_filename),
            mime="text/markdown"
        )

with tab2:
    # Check if viewing a specific artifact
    if st.session_state.viewing_artifact:
        display_artifact(st.session_state.viewing_artifact)
    else:
        render_gallery()
