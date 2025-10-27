"""Artifact gallery and history view"""
import streamlit as st
from utils.file_operations import list_artefacts, load_artefact
import os


def render_gallery():
    """Render the artifact gallery view"""
    st.header("Artifact Gallery")
    st.markdown("Browse and manage your previously generated artifacts")

    # Get list of artifacts
    artefacts = list_artefacts()

    if not artefacts:
        st.info("No artifacts found. Generate your first artifact to see it here!")
        return

    # Display count
    st.markdown(f"**Total artifacts:** {len(artefacts)}")

    # Create filter/sort options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input(
            "Search artifacts",
            placeholder="Search by project name or location...",
            label_visibility="collapsed"
        )
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest First", "Oldest First", "Project Name"],
            label_visibility="collapsed"
        )

    # Filter artifacts based on search
    if search_term:
        artefacts = [
            a for a in artefacts
            if search_term.lower() in a['project'].lower()
            or search_term.lower() in a['location'].lower()
        ]

    # Sort artifacts
    if sort_by == "Oldest First":
        artefacts = list(reversed(artefacts))
    elif sort_by == "Project Name":
        artefacts = sorted(artefacts, key=lambda x: x['project'])

    # Display artifacts in a grid
    for idx, artifact in enumerate(artefacts):
        with st.expander(
            f"**{artifact['project'][:80]}{'...' if len(artifact['project']) > 80 else ''}**",
            expanded=False
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Location:** {artifact['location']}")
                st.markdown(f"**Created:** {artifact['created'].strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**Model:** {artifact['model']}")
                st.markdown(f"**Size:** {artifact['size'] / 1024:.1f} KB")

            with col2:
                # View button
                if st.button("View", key=f"view_{idx}"):
                    st.session_state.viewing_artifact = artifact['filepath']
                    st.session_state.show_gallery = False
                    st.rerun()

                # Download button
                try:
                    content = load_artefact(artifact['filepath'])
                    st.download_button(
                        "Download",
                        data=content,
                        file_name=artifact['filename'],
                        mime="text/markdown",
                        key=f"download_{idx}"
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")

            # Add a subtle divider
            if idx < len(artefacts) - 1:
                st.markdown("---")


def display_artifact(filepath: str):
    """Display a single artifact"""
    try:
        content = load_artefact(filepath)

        # Add a back button
        if st.button("← Back to Gallery"):
            st.session_state.viewing_artifact = None
            st.session_state.show_gallery = True
            st.rerun()

        # Display the artifact content
        st.markdown(content, unsafe_allow_html=True)

        # Download button at the bottom
        st.download_button(
            "Download Artifact",
            data=content,
            file_name=os.path.basename(filepath),
            mime="text/markdown"
        )

    except Exception as e:
        st.error(f"Error loading artifact: {str(e)}")
        if st.button("← Back to Gallery"):
            st.session_state.viewing_artifact = None
            st.session_state.show_gallery = True
            st.rerun()
