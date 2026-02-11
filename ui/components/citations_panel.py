"""
Citations panel component for the RAG Chatbot UI.

Displays detailed citation information with clickable links that navigate
directly to the specific page in the PDF document.
"""

import streamlit as st
from typing import List, Dict, Any
import os


def get_clean_filename(source_file: str) -> str:
    """
    Extract clean filename from full path.
    Removes directory paths and common prefixes.

    Args:
        source_file: Full file path or name

    Returns:
        Clean, readable filename
    """
    # Get just the filename without path
    filename = os.path.basename(source_file)
    # Remove common prefixes
    for prefix in ['raw/', 'processed/', 'documents/']:
        filename = filename.replace(prefix, '')
    return filename


def get_page_url(source_url: str, page_number: int) -> str:
    """
    Generate URL with page anchor for direct navigation.

    Args:
        source_url: Base URL of the PDF
        page_number: Page number to navigate to

    Returns:
        URL with page fragment for direct navigation
    """
    if not source_url:
        return ""

    # Remove any existing fragment
    base_url = source_url.split('#')[0]

    # Add page fragment (works with most PDF viewers)
    # #page=N is standard for PDF.js and most browsers
    if page_number and str(page_number).isdigit():
        return f"{base_url}#page={page_number}"

    return base_url


def render_citations_panel(
    citations: List[Dict[str, Any]],
    out_of_context: bool = False
):
    """
    Render a detailed citations panel.

    Args:
        citations: List of citation dictionaries
        out_of_context: Whether the question was outside document scope
    """
    st.subheader("📚 Sources")

    if out_of_context:
        st.error(
            "No supporting sources found in the provided documents. "
            "The question appears to be outside the scope of the available materials."
        )
        return

    if not citations:
        st.info("No citations available for this response.")
        return

    for i, citation in enumerate(citations, 1):
        with st.container():
            source_file = citation.get("source_file", "Unknown Document")
            page_number = citation.get("page_number", "?")
            source_url = citation.get("source_url", "")
            snippet = citation.get("snippet", "")

            # Clean filename for display
            clean_name = get_clean_filename(source_file)

            # Generate direct page link
            page_url = get_page_url(source_url, page_number)

            col1, col2 = st.columns([4, 1])

            with col1:
                # Display clean filename with page
                st.markdown(f"**{i}. {clean_name}**")
                st.caption(f"📄 Page {page_number}")

            with col2:
                if page_url:
                    st.link_button(
                        f"Page {page_number}",
                        page_url,
                        use_container_width=True,
                        help=f"Open {clean_name} at page {page_number}"
                    )

            # Show snippet with highlighting
            if snippet:
                st.markdown(
                    f'<div style="background: linear-gradient(135deg, #fef9e7 0%, #fef3c7 100%); '
                    f'padding: 12px 15px; border-radius: 8px; margin: 8px 0; '
                    f'border-left: 4px solid #f59e0b; font-size: 0.9rem;">'
                    f'<em>"{snippet}"</em></div>',
                    unsafe_allow_html=True
                )

            if i < len(citations):
                st.divider()


def render_citation_card(citation: Dict[str, Any], index: int):
    """
    Render a single citation as a card with direct page navigation.

    Args:
        citation: Citation dictionary
        index: Citation index for display
    """
    source_file = citation.get("source_file", "Unknown")
    page_number = citation.get("page_number", "?")
    source_url = citation.get("source_url", "")
    snippet = citation.get("snippet", "")

    # Clean filename and generate page URL
    clean_name = get_clean_filename(source_file)
    page_url = get_page_url(source_url, page_number)

    with st.container():
        st.markdown(
            f"""
            <div style="border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px; margin: 10px 0;
                        background: #ffffff; border-left: 4px solid #1e3a5f;">
                <h4 style="margin: 0 0 8px 0; color: #1e3a5f; font-size: 0.95rem;">
                    [{index}] {clean_name}
                </h4>
                <p style="color: #718096; margin: 5px 0; font-size: 0.85rem;">
                    📄 Page {page_number}
                </p>
                {f'<div style="background: linear-gradient(135deg, #fef9e7 0%, #fef3c7 100%); padding: 10px 12px; border-radius: 6px; margin: 10px 0; border-left: 3px solid #f59e0b;"><p style="font-style: italic; color: #44403c; margin: 0; font-size: 0.9rem;">"{snippet}"</p></div>' if snippet else ''}
                {f'<a href="{page_url}" target="_blank" style="display: inline-block; background: #f26522; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; font-weight: 600;">Open Page {page_number}</a>' if page_url else ''}
            </div>
            """,
            unsafe_allow_html=True
        )
