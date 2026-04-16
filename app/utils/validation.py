"""
Input validation utilities.
"""
import re
import os
from typing import Optional


def is_valid_email(email: str) -> bool:
    """RFC 5322 simplified email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def is_valid_uuid(value: str) -> bool:
    """Validate UUID4 format."""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    return bool(re.match(pattern, value, re.IGNORECASE))


def validate_file_extension(filename: str, allowed: set = None) -> bool:
    """Check file extension against allowed set."""
    if allowed is None:
        allowed = {".pdf", ".docx", ".txt"}
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed


def validate_file_size(size_bytes: int, max_mb: int = 10) -> bool:
    """Check that file size is within limits."""
    return 0 < size_bytes <= max_mb * 1024 * 1024


def sanitize_query(query: str, max_length: int = 2000) -> str:
    """Sanitize user query input: strip, truncate, remove control chars."""
    if not query:
        return ""
    # Remove control characters
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)
    return query.strip()[:max_length]


def validate_job_url(url: str) -> Optional[str]:
    """
    Validate and identify the platform from a job posting URL.
    Returns platform name or None if not supported.
    """
    if not is_valid_url(url):
        return None

    url_lower = url.lower()
    platforms = {
        "linkedin.com": "linkedin",
        "indeed.com": "indeed",
        "glassdoor.com": "glassdoor",
    }
    for domain, platform in platforms.items():
        if domain in url_lower:
            return platform
    return None
