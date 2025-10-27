"""Image upload UI components for vision-enhanced generation"""
import streamlit as st
from typing import List
from utils.image_processing import (
    prepare_images_for_api,
    estimate_vision_tokens,
    create_image_description
)


def render_image_upload_section() -> tuple:
    """
    Render the image upload section

    Returns:
        Tuple of (uploaded_files, use_vision)
    """
    with st.expander("📸 Visual Context (Optional - Requires Anthropic Claude)", expanded=False):
        st.markdown("""
Upload sketches, diagrams, site photos, or reference images to enrich your artifact generation.
Claude will analyze these visuals using AI vision and incorporate spatial, material, and contextual insights.

**Works best with:**
- Concept sketches and drawings with annotations
- Site plans showing spatial relationships
- Diagrams showing workflows or connections
- Context photographs of site conditions
- Material references and mood boards
        """)

        uploaded_files = st.file_uploader(
            "Upload images (PNG, JPG, JPEG, WEBP)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            help="Upload up to 5 images. Each image should be under 20MB."
        )

        use_vision = st.checkbox(
            "Use AI vision to interpret images",
            value=True if uploaded_files else False,
            disabled=not uploaded_files,
            help="Enable vision analysis to extract spatial, material, and contextual information from images"
        )

        if uploaded_files and use_vision:
            st.info(f"📊 {len(uploaded_files)} image(s) uploaded • Estimated: ~{estimate_vision_tokens(len(uploaded_files))} additional tokens")

        return uploaded_files, use_vision


def display_image_previews(uploaded_files: List) -> None:
    """
    Display preview thumbnails of uploaded images

    Args:
        uploaded_files: List of Streamlit UploadedFile objects
    """
    if not uploaded_files:
        return

    st.markdown("### Uploaded Images")

    # Create columns for image grid
    cols_per_row = 3
    cols = st.columns(cols_per_row)

    for idx, uploaded_file in enumerate(uploaded_files):
        col_idx = idx % cols_per_row

        with cols[col_idx]:
            # Display image
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

            # Display file info
            file_size_kb = uploaded_file.size / 1024
            st.caption(f"{file_size_kb:.1f} KB")


def display_vision_interpretation(interpretation: str) -> None:
    """
    Display the AI's interpretation of the visual materials

    Args:
        interpretation: The vision interpretation text
    """
    with st.expander("🔍 Visual Analysis", expanded=False):
        st.markdown("### AI's Interpretation of Visual Materials")
        st.markdown(interpretation)
        st.caption("This analysis was extracted from the <think> tags in the AI's response")


def render_vision_status_messages(
    uploaded_files: List,
    use_vision: bool,
    model_config: dict
) -> bool:
    """
    Render status messages about vision feature usage

    Args:
        uploaded_files: List of uploaded files
        use_vision: Whether vision is enabled
        model_config: Current model configuration

    Returns:
        Whether vision can be used (provider supports it)
    """
    provider = model_config.get('provider', '')

    # Check if provider supports vision (Anthropic only)
    vision_supported = provider == 'anthropic'

    if uploaded_files and use_vision:
        if not vision_supported:
            st.error(f"""
⚠️ Vision features are only supported with Anthropic Claude

**Current provider:** {provider}

**To use vision:**
- Switch to **Anthropic Claude** in the sidebar
- Or continue without vision analysis (text-only generation)

**Why Anthropic?** Claude has excellent vision capabilities for analyzing architectural sketches,
diagrams, annotations, and understanding spatial relationships.
            """)
            return False

        st.success(f"""
✅ Vision analysis enabled with Anthropic Claude
Claude will analyze your images and incorporate visual insights into the artifact.
            """)

    return vision_supported


def extract_think_content(response: str) -> tuple:
    """
    Extract thinking/analysis content from response

    Args:
        response: Full response with <think> tags

    Returns:
        Tuple of (artifact_content, think_content)
    """
    import re

    # Try to extract think tags
    think_pattern = r'<think>(.*?)</think>'
    think_match = re.search(think_pattern, response, re.DOTALL)

    if think_match:
        think_content = think_match.group(1).strip()
        # Remove think tags from main content
        artifact_content = re.sub(think_pattern, '', response, flags=re.DOTALL).strip()
        return artifact_content, think_content
    else:
        return response, None
