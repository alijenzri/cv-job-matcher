"""
Text processing utilities for CV and job description normalization.
"""
import re
import unicodedata
from typing import List


def normalize_text(text: str) -> str:
    """Normalize whitespace, strip, and lowercase."""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()


def clean_text(text: str) -> str:
    """Remove non-printable chars and excessive whitespace, preserving case."""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def truncate(text: str, max_length: int = 512) -> str:
    """Truncate text to max_length, breaking at word boundary."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:
        return truncated[:last_space] + "..."
    return truncated + "..."


def extract_skills(text: str, skill_list: List[str] = None) -> List[str]:
    """
    Extract skills from text by matching against a known skill list.
    If no skill_list is provided, uses a sensible default.
    """
    if skill_list is None:
        skill_list = [
            "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
            "react", "angular", "vue", "next.js", "node.js", "django", "fastapi", "flask",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
            "git", "linux", "ci/cd", "devops", "microservices", "rest api", "graphql",
            "machine learning", "deep learning", "nlp", "computer vision",
            "pytorch", "tensorflow", "pandas", "numpy", "scikit-learn",
            "html", "css", "tailwind", "figma", "agile", "scrum",
        ]

    text_lower = text.lower()
    found = []
    for skill in skill_list:
        # Word boundary matching to avoid partial matches
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Simple Jaccard similarity between two texts (word-level).
    Useful for quick pre-filtering before expensive ML models.
    """
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for embedding.
    Important for long CVs that exceed model context windows.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > chunk_size * 0.5:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1

        chunks.append(chunk.strip())
        start = end - overlap

    return chunks
