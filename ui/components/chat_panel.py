"""
Chat panel component for the RAG Chatbot UI.

Handles chat history display and message rendering with enterprise styling.
"""

import streamlit as st
from typing import List, Dict, Any, Optional

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


def initialize_chat_history():
    """Initialize chat history in session state if not present."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    else:
        # Clean up any corrupted messages (e.g., raw HTML)
        clean_messages = []
        for msg in st.session_state.messages:
            content = msg.get("content", "")
            # Skip messages that look like raw HTML (contain HTML tags)
            if isinstance(content, str) and not (
                content.strip().startswith("<div") or
                content.strip().startswith("<span") or
                content.strip().startswith("<h1") or
                "class=" in content[:100] if len(content) > 100 else "class=" in content
            ):
                clean_messages.append(msg)
        st.session_state.messages = clean_messages


def add_user_message(message: str):
    """Add a user message to chat history."""
    st.session_state.messages.append({
        "role": "user",
        "content": message
    })


def add_assistant_message(
    message: str,
    citations: Optional[List[Dict[str, Any]]] = None,
    out_of_context: bool = False
):
    """Add an assistant message with optional citations to chat history."""
    st.session_state.messages.append({
        "role": "assistant",
        "content": message,
        "citations": citations or [],
        "out_of_context": out_of_context
    })


def render_chat_history():
    """Render the chat history in the main panel."""
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
                    # Don't show citations for no-info responses
                elif citations:
                    render_inline_citations(citations)


def render_inline_citations(citations: List[Dict[str, Any]]):
    """Render citations inline after an assistant message."""
    if not citations:
        return

    with st.expander(f"Sources ({len(citations)} citations)", expanded=False):
        for i, citation in enumerate(citations, 1):
            col1, col2 = st.columns([4, 1])

            with col1:
                source_file = citation.get('source_file', 'Unknown')
                # Clean up path for display
                display_name = source_file.replace('raw/', '').replace('processed/', '')
                page_number = citation.get('page_number', '?')

                st.markdown(f"**[{i}] {display_name}** — Page {page_number}")

                snippet = citation.get("snippet", "")
                if snippet:
                    st.caption(f'"{snippet}"')

            with col2:
                source_url = citation.get("source_url", "")
                if source_url:
                    st.link_button(
                        "Open",
                        source_url,
                        use_container_width=True
                    )

            if i < len(citations):
                st.divider()


def clear_chat_history():
    """Clear the chat history."""
    st.session_state.messages = []
