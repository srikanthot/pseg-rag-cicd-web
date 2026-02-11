"""
Sidebar controls component for the RAG Chatbot UI.

Provides configuration options for client-facing enterprise application.
"""

import streamlit as st
import requests
from typing import Tuple

# PSEG SVG Logo for sidebar (navy text for light background)
SIDEBAR_LOGO_SVG = '''
<svg viewBox="0 0 180 45" xmlns="http://www.w3.org/2000/svg" style="height: 32px; width: auto;">
  <g transform="translate(18, 22)">
    <circle cx="0" cy="0" r="16" fill="#f26522"/>
    <g fill="white">
      <polygon points="0,-13 1,-6 -1,-6"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(30)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(60)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(90)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(120)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(150)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(180)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(210)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(240)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(270)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(300)"/>
      <polygon points="0,-13 1,-6 -1,-6" transform="rotate(330)"/>
    </g>
    <circle cx="0" cy="0" r="4" fill="white"/>
  </g>
  <text x="42" y="28" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#1e3a5f">PSEG</text>
</svg>
'''


def render_sidebar(backend_url: str) -> Tuple[int, bool, float]:
    """
    Render the sidebar with all controls.

    Args:
        backend_url: URL of the backend API

    Returns:
        Tuple of (top_k, strict_mode, threshold)
    """
    with st.sidebar:
        # Sidebar brand header with SVG logo
        st.markdown(f'''
            <div style="padding: 0.5rem 0 0.75rem 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 0.75rem;">
                {SIDEBAR_LOGO_SVG}
            </div>
        ''', unsafe_allow_html=True)

        st.caption("Enterprise Document Q&A System")

        st.divider()

        # Search Settings Section
        st.markdown("### Search Settings")

        top_k = st.slider(
            "Number of sources",
            min_value=1,
            max_value=15,
            value=5,
            help="Number of document chunks to retrieve for each question. Higher values provide more context but may slow down responses."
        )

        strict_mode = st.toggle(
            "Strict Grounding",
            value=True,
            help="When enabled, the assistant will only answer questions that can be grounded in the documents. Prevents hallucinations."
        )

        threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=0.5,
            value=0.01,
            step=0.01,
            format="%.2f",
            help="Minimum relevance score required. Lower values are more permissive.",
            disabled=not strict_mode
        )

        st.divider()

        # System Status (simplified for clients)
        render_health_status(backend_url)

        st.divider()

        # Clear Chat Action
        if st.button("🗑️ Clear Conversation", use_container_width=True, help="Start a new conversation"):
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # Help section (client-focused)
        with st.expander("💡 Help & Tips"):
            st.markdown("""
            **How to use:**
            1. Type your question in the chat input below
            2. The assistant searches through technical documents
            3. Get accurate answers with source citations

            **Tips for better results:**
            - Be specific in your questions
            - Reference document topics directly
            - Use technical terminology from the manuals
            - Click on citations to view the source document

            **Understanding Citations:**
            - Each answer includes source references
            - Click the citation link to open the exact page
            - Citations show the document name and page number
            """)

        return top_k, strict_mode, threshold


def render_health_status(backend_url: str):
    """Render simplified system status for clients."""
    st.markdown("### System Status")

    try:
        response = requests.get(f"{backend_url}/health", timeout=5)

        if response.status_code == 200:
            health = response.json()
            status = health.get('status', 'unknown')

            if status in ('ok', 'healthy'):
                st.success("✓ System Online")
            else:
                st.warning("⚠ System experiencing issues")
        else:
            st.error("✗ System Unavailable")

    except requests.exceptions.ConnectionError:
        st.error("✗ System Unavailable")
        st.caption("Please try again later or contact support")
    except Exception:
        st.warning("⚠ Unable to check system status")
