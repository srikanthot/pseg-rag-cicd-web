"""
Streamlit UI for the PSEG Tech Manual Assistant.

A professional, enterprise-ready interface for technical document Q&A
with citations and strict grounding.
"""

import os
import streamlit as st
import requests
from typing import Optional

from components.chat_panel import (
    initialize_chat_history,
    add_user_message,
    add_assistant_message,
    clear_chat_history,
)
from components.citations_panel import (
    render_citations_panel,
    get_clean_filename,
    get_page_url,
)
from components.sidebar_controls import render_sidebar

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def initialize_view_settings():
    """Initialize view settings in session state."""
    if "mobile_view" not in st.session_state:
        st.session_state.mobile_view = False
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}  # {message_id: "up" | "down" | None}
    if "message_ids" not in st.session_state:
        st.session_state.message_ids = []  # Track message IDs for feedback


def get_view_css():
    """Get CSS based on current view mode."""
    if st.session_state.get("mobile_view", False):
        return """
        <style>
            /* Mobile View - Compact Layout */
            .main .block-container {
                max-width: 420px !important;
                padding: 0.75rem 1rem !important;
                margin: 0 auto !important;
            }

            /* Compact chat messages */
            [data-testid="stChatMessage"] {
                padding: 0.5rem 0.75rem !important;
                border-radius: 12px !important;
                margin: 0.25rem 0 !important;
            }

            [data-testid="stChatMessage"] p {
                font-size: 0.9rem !important;
                line-height: 1.4 !important;
            }

            /* Compact chat input */
            [data-testid="stChatInput"] {
                border-radius: 24px !important;
            }

            [data-testid="stChatInput"] textarea {
                font-size: 0.9rem !important;
                padding: 0.5rem !important;
            }

            /* Compact header */
            .pseg-header {
                padding: 0.75rem 1rem !important;
                border-radius: 14px !important;
                margin-bottom: 0.75rem !important;
            }

            .pseg-header .header-title {
                font-size: 1.1rem !important;
            }

            .pseg-header .header-subtitle {
                font-size: 0.8rem !important;
            }

            .pseg-header .header-badges {
                display: none !important;
            }

            .pseg-header svg {
                height: 36px !important;
            }

            /* Compact expander */
            .streamlit-expanderHeader {
                font-size: 0.85rem !important;
                padding: 0.4rem 0.6rem !important;
            }

            /* Compact buttons */
            .stButton > button {
                padding: 0.35rem 0.7rem !important;
                font-size: 0.8rem !important;
                border-radius: 8px !important;
            }

            /* Hide sidebar by default in mobile */
            [data-testid="stSidebar"] {
                min-width: 240px !important;
                max-width: 240px !important;
            }

            /* Smaller column gaps */
            [data-testid="column"] {
                padding: 0 0.25rem !important;
            }

            /* Compact footer */
            .main > div:last-child {
                font-size: 0.7rem !important;
            }
        </style>
        """
    else:
        return ""

st.set_page_config(
    page_title="PSEG Tech Manual Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PSEG Enterprise Theme
st.markdown("""
<style>
    :root {
        --pseg-navy: #1e3a5f;
        --pseg-navy-light: #2d5a87;
        --pseg-orange: #f26522;
        --bg-page: #f7f9fc;
        --bg-card: #ffffff;
        --border-color: #e2e8f0;
        --text-primary: #1a1a2e;
        --text-muted: #718096;
    }

    .stApp {
        background: var(--bg-page) !important;
    }

    .main .block-container {
        padding: 1.5rem 2rem 2rem !important;
        max-width: 1300px;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        padding: 1rem 1.25rem;
        border-radius: 14px;
        margin: 0.6rem 0;
        box-shadow: 0 1px 3px rgba(30, 58, 95, 0.06);
    }

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar-user"]) {
        background: linear-gradient(135deg, #eef4fb 0%, #e3ecf7 100%);
        border: 1px solid #d0dff0;
        border-left: 4px solid #4a90d9;
    }

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar-assistant"]) {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--pseg-navy);
    }

    [data-testid="stChatInput"] {
        background: var(--bg-card) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 14px !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: var(--pseg-navy) !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--pseg-navy) 0%, var(--pseg-navy-light) 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
    }

    .stLinkButton > a {
        background: var(--pseg-orange) !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-card) !important;
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--pseg-navy);
    }

    /* Alerts */
    .stWarning {
        background: #fffbeb !important;
        border: 1px solid #fde68a !important;
        border-left: 4px solid var(--pseg-orange) !important;
        border-radius: 10px !important;
    }

    .stInfo {
        background: #eff6ff !important;
        border: 1px solid #bfdbfe !important;
        border-left: 4px solid var(--pseg-navy) !important;
        border-radius: 10px !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid #edf2f7 !important;
        border-radius: 10px !important;
        color: var(--pseg-navy) !important;
    }

    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid #edf2f7 !important;
        border-top: none !important;
    }

    /* Form elements */
    .stSlider > div > div {
        background: linear-gradient(90deg, var(--pseg-navy), var(--pseg-orange)) !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--pseg-orange) !important;
    }

    hr {
        border: none;
        height: 1px;
        background: #edf2f7;
        margin: 1rem 0;
    }

    /* View Toggle Styles */
    .view-toggle-container {
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(255,255,255,0.1);
        padding: 6px 12px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.2);
    }

    .view-toggle-label {
        font-size: 0.8rem;
        color: white;
        font-weight: 500;
    }

    /* Feedback Button Styles */
    .feedback-container {
        display: flex;
        gap: 8px;
        margin-top: 8px;
        padding-top: 8px;
    }

    .feedback-btn {
        background: transparent;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 6px 12px;
        cursor: pointer;
        font-size: 1rem;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .feedback-btn:hover {
        background: #f7fafc;
        border-color: #cbd5e0;
    }

    .feedback-btn.active-up {
        background: #c6f6d5 !important;
        border-color: #38a169 !important;
        color: #22543d;
    }

    .feedback-btn.active-down {
        background: #fed7d7 !important;
        border-color: #e53e3e !important;
        color: #742a2a;
    }

    .feedback-btn .icon {
        font-size: 1.1rem;
    }

    .feedback-text {
        font-size: 0.75rem;
        color: #718096;
        margin-left: 8px;
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
    answer_lower = answer.lower()
    return any(phrase in answer_lower for phrase in NO_INFO_PHRASES)


def send_chat_request(
    question: str,
    top_k: int,
    backend_url: str,
    conversation_history: Optional[list] = None
) -> Optional[dict]:
    """Send a chat request to the backend API with conversation history."""
    try:
        payload = {"question": question, "top_k": top_k}
        if conversation_history:
            payload["conversation_history"] = conversation_history

        response = requests.post(
            f"{backend_url}/api/chat",
            json=payload,
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


def render_header():
    """Render the PSEG branded header using native Streamlit."""
    # Header container with custom styling
    is_mobile = st.session_state.get("mobile_view", False)

    st.markdown(f"""
    <div class="pseg-header" style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
                border-radius: 18px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
                box-shadow: 0 8px 24px rgba(30, 58, 95, 0.12);
                border-bottom: 4px solid #f26522;">
        <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
            <svg viewBox="0 0 180 50" xmlns="http://www.w3.org/2000/svg" style="height: {'40px' if is_mobile else '50px'}; width: auto; flex-shrink: 0;">
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
            <div style="flex: 1;">
                <div class="header-title" style="font-size: {'1.1rem' if is_mobile else '1.4rem'}; font-weight: 700; color: white; margin-bottom: 4px;">
                    Tech Manual Assistant
                </div>
                <div class="header-subtitle" style="font-size: {'0.8rem' if is_mobile else '0.9rem'}; color: rgba(255,255,255,0.85);">
                    Your intelligent assistant for technical documentation
                </div>
                <div class="header-badges" style="display: {'none' if is_mobile else 'flex'}; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                    <span style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px;
                                 font-size: 0.75rem; color: white; border: 1px solid rgba(255,255,255,0.2);">
                        AI-Powered
                    </span>
                    <span style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px;
                                 font-size: 0.75rem; color: white; border: 1px solid rgba(255,255,255,0.2);">
                        Citation-Backed
                    </span>
                    <span style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px;
                                 font-size: 0.75rem; color: white; border: 1px solid rgba(255,255,255,0.2);">
                        Enterprise Secure
                    </span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_feedback_buttons(message_idx: int):
    """Render thumbs up/down feedback buttons for a message."""
    feedback_key = f"feedback_{message_idx}"
    current_feedback = st.session_state.feedback.get(feedback_key, None)

    col1, col2, col3 = st.columns([1, 1, 10])

    with col1:
        # Thumbs up button
        up_type = "primary" if current_feedback == "up" else "secondary"
        if st.button("👍", key=f"up_{message_idx}", type=up_type, help="This response was helpful"):
            if current_feedback == "up":
                st.session_state.feedback[feedback_key] = None
            else:
                st.session_state.feedback[feedback_key] = "up"
            st.rerun()

    with col2:
        # Thumbs down button
        down_type = "primary" if current_feedback == "down" else "secondary"
        if st.button("👎", key=f"down_{message_idx}", type=down_type, help="This response was not helpful"):
            if current_feedback == "down":
                st.session_state.feedback[feedback_key] = None
            else:
                st.session_state.feedback[feedback_key] = "down"
            st.rerun()

    with col3:
        if current_feedback == "up":
            st.caption("Thanks for the feedback!")
        elif current_feedback == "down":
            st.caption("Thanks! We'll work to improve.")


def render_chat_history_with_feedback():
    """Render the chat history with feedback buttons for assistant messages."""
    assistant_msg_idx = 0

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                citations = message.get("citations", [])
                out_of_context = message.get("out_of_context", False)
                content = message.get("content", "")

                # Check if answer indicates no relevant info
                no_relevant_info = out_of_context or is_no_info_response(content)

                if no_relevant_info:
                    st.warning(
                        "This question appears to be outside the scope of the available documents."
                    )
                elif citations:
                    # Render inline citations with clean filenames and direct page links
                    with st.expander(f"📚 Sources ({len(citations)})", expanded=False):
                        for i, citation in enumerate(citations, 1):
                            cite_col1, cite_col2 = st.columns([4, 1])

                            source_file = citation.get('source_file', 'Unknown')
                            page_number = citation.get('page_number', '?')
                            source_url = citation.get("source_url", "")

                            # Clean filename and generate page URL
                            clean_name = get_clean_filename(source_file)
                            page_url = get_page_url(source_url, page_number)

                            with cite_col1:
                                st.markdown(f"**[{i}] {clean_name}**")
                                st.caption(f"📄 Page {page_number}")

                                snippet = citation.get("snippet", "")
                                if snippet:
                                    st.markdown(
                                        f'<div style="background: linear-gradient(135deg, #fef9e7 0%, #fef3c7 100%); '
                                        f'padding: 8px 10px; border-radius: 6px; margin: 4px 0; '
                                        f'border-left: 3px solid #f59e0b; font-size: 0.85rem;">'
                                        f'<em>"{snippet}"</em></div>',
                                        unsafe_allow_html=True
                                    )

                            with cite_col2:
                                if page_url:
                                    st.link_button(
                                        f"Page {page_number}",
                                        page_url,
                                        use_container_width=True,
                                        help=f"Open {clean_name} at page {page_number}"
                                    )

                            if i < len(citations):
                                st.divider()

                # Render feedback buttons for all assistant messages
                render_feedback_buttons(assistant_msg_idx)
                assistant_msg_idx += 1


def render_view_toggle():
    """Render the mobile/desktop view toggle."""
    is_mobile = st.session_state.get("mobile_view", False)

    col1, col2 = st.columns([6, 1])
    with col2:
        # Create a nice toggle with icon
        view_label = "📱 Mobile" if is_mobile else "🖥️ Desktop"
        if st.toggle(
            view_label,
            value=is_mobile,
            key="view_toggle",
            help="Switch between mobile and desktop view"
        ):
            if not st.session_state.mobile_view:
                st.session_state.mobile_view = True
                st.rerun()
        else:
            if st.session_state.mobile_view:
                st.session_state.mobile_view = False
                st.rerun()


def main():
    """Main application entry point."""
    initialize_chat_history()
    initialize_view_settings()

    # Apply view-specific CSS
    st.markdown(get_view_css(), unsafe_allow_html=True)

    # Render sidebar and get settings
    top_k, strict_mode, threshold = render_sidebar(BACKEND_URL)

    # Render view toggle
    render_view_toggle()

    # Render PSEG branded header
    render_header()

    # Render chat history with feedback buttons
    render_chat_history_with_feedback()

    # Chat input
    if prompt := st.chat_input("Ask a question about PSEG technical manuals..."):
        add_user_message(prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching documents..."):
                # Build conversation history from session state (exclude the current message)
                history = []
                for msg in st.session_state.messages[:-1]:  # Exclude the just-added user message
                    history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

                response = send_chat_request(prompt, top_k, BACKEND_URL, history if history else None)

                if response:
                    answer = response.get("answer", "No response generated.")
                    citations = response.get("citations", [])
                    out_of_context = response.get("out_of_context", False)
                    chunks_count = response.get("retrieved_chunks_count", 0)

                    st.markdown(answer)

                    # Check if answer indicates no relevant info (even if out_of_context is False)
                    no_relevant_info = out_of_context or is_no_info_response(answer)

                    if no_relevant_info:
                        st.warning(
                            "This question appears to be outside the scope of the available documents."
                        )
                        # Don't show or save citations for out-of-context responses
                        add_assistant_message(answer, [], True)
                    elif citations:
                        st.markdown("---")
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
                                        st.markdown(
                                            f'<div style="background: linear-gradient(135deg, #fef9e7 0%, #fef3c7 100%); '
                                            f'padding: 8px 10px; border-radius: 6px; margin: 4px 0; '
                                            f'border-left: 3px solid #f59e0b; font-size: 0.85rem;">'
                                            f'<em>"{snippet}"</em></div>',
                                            unsafe_allow_html=True
                                        )

                                with col2:
                                    if page_url:
                                        st.link_button(
                                            f"Page {page_number}",
                                            page_url,
                                            use_container_width=True,
                                            help=f"Open {clean_name} at page {page_number}"
                                        )

                                if i < len(citations):
                                    st.divider()

                        add_assistant_message(answer, citations, False)
                    else:
                        add_assistant_message(answer, [], False)
                else:
                    error_msg = "Failed to get a response. Please check the backend connection."
                    st.error(error_msg)
                    add_assistant_message(error_msg, [], True)

    # Footer
    st.markdown(
        '<div style="text-align: center; padding: 1rem 0; margin-top: 1.5rem; color: #718096; font-size: 0.8rem;">'
        'PSEG Tech Manual Assistant — Powered by Azure AI</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
