"""
File utilities: safe upload handling, temp directory management, MIME validation.
"""
import os
import shutil
import hashlib
import mimetypes
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

ALLOWED_MIMES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


def save_upload_file(upload_file, destination: str) -> str:
    """
    Save an uploaded file to disk safely.
    Returns the final file path.
    """
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        logger.info(f"Saved upload: {destination} ({os.path.getsize(destination)} bytes)")
        return destination
    finally:
        upload_file.file.close()


def get_file_hash(file_path: str) -> str:
    """SHA-256 hash of a file for deduplication."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_file_type(filename: str) -> bool:
    """Check if file extension is in the allowed list."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_MIMES


def get_mime_type(filename: str) -> Optional[str]:
    """Get MIME type from filename."""
    mime, _ = mimetypes.guess_type(filename)
    return mime


def ensure_dir(path: str) -> str:
    """Create directory if it doesn't exist, return the path."""
    os.makedirs(path, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Strip directory components
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric chars except dots, hyphens, underscores
    import re
    filename = re.sub(r'[^\w\-.]', '_', filename)
    return filename


def cleanup_temp_files(directory: str, max_age_hours: int = 24):
    """Remove temp files older than max_age_hours."""
    import time
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    count = 0
    for f in Path(directory).glob("*"):
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink()
            count += 1
    if count:
        logger.info(f"Cleaned up {count} temp files from {directory}")
