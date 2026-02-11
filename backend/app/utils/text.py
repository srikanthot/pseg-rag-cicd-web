"""
Text processing utilities for the RAG Chatbot.

Provides helper functions for text cleaning and manipulation.
"""

import re
from typing import Optional


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing excessive whitespace and normalizing.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text with normalized whitespace
    """
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, preserving word boundaries.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 500)
        suffix: Suffix to add when truncated (default "...")
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.7:
        truncated = truncated[:last_space]
    
    return truncated.rstrip() + suffix


def extract_sentences(text: str, max_sentences: int = 3) -> str:
    """
    Extract the first N sentences from text.
    
    Args:
        text: Source text
        max_sentences: Maximum number of sentences to extract
        
    Returns:
        Extracted sentences
    """
    if not text:
        return ""
    
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    
    selected = sentences[:max_sentences]
    result = ' '.join(selected)
    
    if not result.endswith(('.', '!', '?')):
        result = result.rstrip() + '.'
    
    return result
