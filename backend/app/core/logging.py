"""
Safe logging configuration for the RAG Chatbot application.

Ensures no secrets are logged and provides consistent logging format.
"""

import logging
import re
import sys
from typing import Optional


class SecretFilter(logging.Filter):
    """Filter that redacts potential secrets from log messages."""

    SECRET_PATTERNS = [
        r"(api[_-]?key[s]?\s*[=:]\s*)['\"]?[\w\-]+['\"]?",
        r"(password[s]?\s*[=:]\s*)['\"]?[\w\-]+['\"]?",
        r"(secret[s]?\s*[=:]\s*)['\"]?[\w\-]+['\"]?",
        r"(token[s]?\s*[=:]\s*)['\"]?[\w\-]+['\"]?",
        r"(connection[_-]?string[s]?\s*[=:]\s*)['\"]?[^'\";\s]+['\"]?",
        r"(AccountKey=)[^;]+",
        r"(SharedAccessSignature=)[^;]+",
    ]

    def __init__(self):
        super().__init__()
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.SECRET_PATTERNS]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact secrets from log message."""
        if record.msg:
            msg = str(record.msg)
            for pattern in self.patterns:
                msg = pattern.sub(r"\1[REDACTED]", msg)
            record.msg = msg
        return True


def get_logger(name: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """
    Get a configured logger instance with secret filtering.
    
    Args:
        name: Logger name (defaults to root logger)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or "rag_chatbot")
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        handler.addFilter(SecretFilter())
        logger.addHandler(handler)
    
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    
    return logger
