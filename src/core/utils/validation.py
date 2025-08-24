"""
Validation utilities for the RivalSearch Agent.

Provides validation functions for URLs, queries, and other input data.
"""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_query(query: str) -> bool:
    """Validate if a query string is valid.
    
    Args:
        query: Query string to validate
        
    Returns:
        True if valid query, False otherwise
    """
    if not query or not isinstance(query, str):
        return False
    
    # Remove whitespace and check minimum length
    cleaned_query = query.strip()
    if len(cleaned_query) < 3:
        return False
    
    # Check for basic content (not just whitespace or special characters)
    if not re.search(r'[a-zA-Z0-9]', cleaned_query):
        return False
    
    return True


def sanitize_query(query: Optional[str]) -> str:
    """Sanitize a query string.
    
    Args:
        query: Query string to sanitize
        
    Returns:
        Sanitized query string
    """
    if not query:
        return ""
    
    # Remove extra whitespace
    sanitized = re.sub(r'\s+', ' ', query.strip())
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    
    return sanitized
