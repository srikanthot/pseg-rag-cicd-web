"""
Streamlit Mobile UI for the PSEG Tech Manual Assistant.

A mobile-optimized interface centered like a phone screen mirror.
Same functionality as the desktop version.
"""

import os
import streamlit as st
import requests
from typing import Optional, List, Dict, Any

from components.chat_panel import (
    initialize_chat_history,
    add_user_message,
    add_assistant_message,
    clear_chat_history,
)
from components.sidebar_controls import render_sidebar
from components.citations_panel import get_clean_filename, get_page_url

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="PSEG Mobile Assistant",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile Phone Simulation CSS - Light Background
st.markdown("""
<style>
    /* Light background for the page */
    .stApp {
        background: linear-gradient(135deg, #e8f0f8 0%, #d4e4f4 100%) !important;
    }

    /* Hide default streamlit header */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Phone container - centered like screen mirroring */
    .main .block-container {
        max-width: 380px !important;
        min-height: 680px !important;
        padding: 24px 16px 30px 16px !important;
        margin: 25px auto !important;
        background: #ffffff !important;
        border-radius: 45px !important;
        box-shadow:
            0 0 0 3px #e2e8f0,
            0 0 0 6px #cbd5e1,
            0 0 0 8px #94a3b8,
            0 20px 50px rgba(0, 0, 0, 0.15),
            0 10px 20px rgba(0, 0, 0, 0.1) !important;
        position: relative;
        border: 1px solid #e2e8f0;
    }

    /* Phone speaker/camera area at top */
    .main .block-container::before {
        content: "";
        position: absolute;
        top: 12px;
        left: 50%;
        transform: translateX(-50%);
        width: 80px;
        height: 6px;
        background: #e2e8f0;
        border-radius: 3px;
    }

    /* Phone home indicator at bottom */
    .main .block-container::after {
        content: "";
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 4px;
        background: #cbd5e1;
        border-radius: 2px;
    }

    /* Inner content area */
    .block-container > div {
        padding-top: 8px !important;
    }

    /* Mobile chat messages */
    [data-testid="stChatMessage"] {
        padding: 10px 12px !important;
        border-radius: 16px !important;
        margin: 6px 0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }

    [data-testid="stChatMessage"] p {
        font-size: 14px !important;
        line-height: 1.45 !important;
    }

    /* User message */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar-user"]) {
        background: linear-gradient(135deg, #eef4fb 0%, #e3ecf7 100%) !important;
        border: 1px solid #d0dff0 !important;
        border-left: 3px solid #4a90d9 !important;
    }

    /* Assistant message */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar-assistant"]) {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 3px solid #1e3a5f !important;
    }

    /* Chat input */
    [data-testid="stChatInput"] {
        border-radius: 24px !important;
        border: 2px solid #e2e8f0 !important;
        background: #ffffff !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: #1e3a5f !important;
    }

    [data-testid="stChatInput"] textarea {
        font-size: 14px !important;
    }

    /* Buttons */
    .stButton > button {
        padding: 6px 12px !important;
        font-size: 12px !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%) !important;
        color: white !important;
        border: none !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-size: 13px !important;
        padding: 8px 12px !important;
        border-radius: 12px !important;
        background: #f8fafc !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        min-width: 260px !important;
        max-width: 260px !important;
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #1e3a5f !important;
        font-size: 14px !important;
    }

    /* Warning/info boxes */
    .stWarning {
        background: #fffbeb !important;
        border: 1px solid #fde68a !important;
        border-left: 3px solid #f26522 !important;
        border-radius: 10px !important;
        font-size: 12px !important;
        padding: 8px 12px !important;
    }

    .stInfo {
        background: #eff6ff !important;
        border: 1px solid #bfdbfe !important;
        border-left: 3px solid #1e3a5f !important;
        border-radius: 10px !important;
        font-size: 12px !important;
    }

    .stError {
        font-size: 12px !important;
        padding: 8px 12px !important;
        border-radius: 10px !important;
    }

    /* Dividers and spacing */
    hr {
        margin: 8px 0 !important;
        border: none !important;
        height: 1px !important;
        background: #edf2f7 !important;
    }

    /* Captions */
    .stCaption, [data-testid="stCaptionContainer"] {
        font-size: 11px !important;
    }

    /* Link buttons */
    .stLinkButton > a {
        font-size: 11px !important;
        padding: 4px 10px !important;
        background: #f26522 !important;
        color: white !important;
        border-radius: 6px !important;
    }

    /* Columns */
    [data-testid="column"] {
        padding: 0 4px !important;
    }

    /* Slider */
    .stSlider > div > div {
        background: linear-gradient(90deg, #1e3a5f, #f26522) !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #f26522 !important;
    }
</style>
""", unsafe_allow_html=True)

# Phrases that indicate no relevant information found
NO_INFO_PHRASES = [
    "i don't have enough information",
    "i do not have enough information",
    "don't have enough information",
    "do not have enough information",
    "cannot find relevant information",
    "no relevant information",
    "outside the scope",
    "not covered in the documents",
    "not found in the provided",
]


def is_no_info_response(answer: str) -> bool:
    """Check if the answer indicates no relevant information was found."""
    if not answer:
        return False
    answer_lower = answer.lower()
    return any(phrase in answer_lower for phrase in NO_INFO_PHRASES)


def initialize_mobile_state():
    """Initialize mobile-specific session state."""
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}


def send_chat_request(question: str, top_k: int, backend_url: str) -> Optional[dict]:
    """Send a chat request to the backend API."""
    try:
        response = requests.post(
            f"{backend_url}/api/chat",
            json={"question": question, "top_k": top_k},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {backend_url}")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"Error: {type(e).__name__}")
        return None


def render_mobile_header():
    """Render compact mobile header matching PSEG branding."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
                border-radius: 16px; padding: 12px 14px; margin-bottom: 10px;
                box-shadow: 0 4px 12px rgba(30, 58, 95, 0.15);
                border-bottom: 3px solid #f26522;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <svg viewBox="0 0 180 50" xmlns="http://www.w3.org/2000/svg" style="height: 32px; width: auto;">
                <g transform="translate(22, 25)">
                    <circle cx="0" cy="0" r="20" fill="#f26522"/>
                    <g fill="white">
                        <polygon points="0,-17 1.5,-8 -1.5,-8"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(30)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(60)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(90)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(120)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(150)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(180)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(210)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(240)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(270)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(300)"/>
                        <polygon points="0,-17 1.5,-8 -1.5,-8" transform="rotate(330)"/>
                    </g>
                    <circle cx="0" cy="0" r="5" fill="white"/>
                </g>
                <text x="52" y="32" font-family="Arial, sans-serif" font-size="26" font-weight="bold" fill="white">PSEG</text>
            </svg>
            <div>
                <div style="font-size: 14px; font-weight: 700; color: white;">
                    Tech Manual Assistant
                </div>
                <div style="font-size: 10px; color: rgba(255,255,255,0.85);">
                    AI-Powered • Citation-Backed
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_feedback_buttons(msg_idx: int):
    """Render feedback buttons for a message."""
    feedback_key = f"mobile_feedback_{msg_idx}"
    current = st.session_state.feedback.get(feedback_key, None)

    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        btn_type = "primary" if current == "up" else "secondary"
        if st.button("👍", key=f"m_up_{msg_idx}", type=btn_type, help="Helpful"):
            st.session_state.feedback[feedback_key] = None if current == "up" else "up"
            st.rerun()
    with col2:
        btn_type = "primary" if current == "down" else "secondary"
        if st.button("👎", key=f"m_down_{msg_idx}", type=btn_type, help="Not helpful"):
            st.session_state.feedback[feedback_key] = None if current == "down" else "down"
            st.rerun()
    with col3:
        if current == "up":
            st.caption("Thanks for feedback!")
        elif current == "down":
            st.caption("We'll improve!")


def render_citations(citations: List[Dict[str, Any]]):
    """Render citations in mobile format with clean filenames and direct page links."""
    if not citations:
        return

    with st.expander(f"📚 Sources ({len(citations)})", expanded=False):
        for i, citation in enumerate(citations, 1):
            col1, col2 = st.columns([4, 1])

            source_file = citation.get('source_file', 'Unknown')
            page_number = citation.get('page_number', '?')
            source_url = citation.get("source_url", "")

            # Clean filename and generate page URL
            clean_name = get_clean_filename(source_file)
            page_url = get_page_url(source_url, page_number)

            with col1:
                st.markdown(f"**[{i}] {clean_name}**")
                st.caption(f"📄 Page {page_number}")

                snippet = citation.get("snippet", "")
                if snippet:
                    truncated = snippet[:100] + "..." if len(snippet) > 100 else snippet
                    st.markdown(
                        f'<div style="background: linear-gradient(135deg, #fef9e7 0%, #fef3c7 100%); '
                        f'padding: 6px 8px; border-radius: 6px; margin: 4px 0; '
                        f'border-left: 2px solid #f59e0b; font-size: 0.8rem;">'
                        f'<em>"{truncated}"</em></div>',
                        unsafe_allow_html=True
                    )

            with col2:
                if page_url:
                    st.link_button(
                        f"Pg {page_number}",
                        page_url,
                        use_container_width=True,
                        help=f"Open {clean_name} at page {page_number}"
                    )

            if i < len(citations):
                st.divider()


def render_chat_history_with_feedback():
    """Render chat history with feedback buttons."""
    assistant_idx = 0

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                citations = message.get("citations", [])
                out_of_context = message.get("out_of_context", False)
                content = message.get("content", "")

                no_info = out_of_context or is_no_info_response(content)

                if no_info:
                    st.warning("This question appears to be outside the scope of the available documents.")
                elif citations:
                    render_citations(citations)

                render_feedback_buttons(assistant_idx)
                assistant_idx += 1


def main():
    """Main mobile app entry point."""
    initialize_chat_history()
    initialize_mobile_state()

    # Render sidebar with same controls as desktop
    top_k, strict_mode, threshold = render_sidebar(BACKEND_URL)

    # Render mobile header
    render_mobile_header()

    # Render chat history
    render_chat_history_with_feedback()

    # Chat input
    if prompt := st.chat_input("Ask about PSEG manuals..."):
        add_user_message(prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                response = send_chat_request(prompt, top_k, BACKEND_URL)

                if response:
                    answer = response.get("answer", "No response generated.")
                    citations = response.get("citations", [])
                    out_of_context = response.get("out_of_context", False)
                    chunks_count = response.get("retrieved_chunks_count", 0)

                    st.markdown(answer)

                    no_info = out_of_context or is_no_info_response(answer)

                    if no_info:
                        st.warning("This question appears to be outside the scope of the available documents.")
                        add_assistant_message(answer, [], True)
                    elif citations:
                        st.markdown("---")
                        render_citations(citations)
                        add_assistant_message(answer, citations, False)
                    else:
                        add_assistant_message(answer, [], False)
                else:
                    error_msg = "Failed to get response. Check backend connection."
                    st.error(error_msg)
                    add_assistant_message(error_msg, [], True)

    # Footer
    st.markdown(
        '<div style="text-align: center; padding: 6px 0; color: #718096; font-size: 9px;">'
        'PSEG Tech Manual Assistant — Powered by Azure AI</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
