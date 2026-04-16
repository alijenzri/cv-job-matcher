"""
Production embedding service with lazy-loaded singleton model.
Avoids re-initializing the SentenceTransformer on every call.
"""
from sentence_transformers import SentenceTransformer
from app.config import settings
import numpy as np
import logging

logger = logging.getLogger(__name__)

_model = None

def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model as a module-level singleton."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully.")
    return _model


def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for a single text string."""
    model = _get_model()
    return model.encode(text, show_progress_bar=False).tolist()


def get_embeddings_batch(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """
    Generate embedding vectors for a batch of texts.
    Uses internal batching for GPU/CPU efficiency.
    """
    if not texts:
        return []
    model = _get_model()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    return embeddings.tolist()
