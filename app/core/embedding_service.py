"""
Production embedding service (core module).
Re-exports from ml/utils/embeddings for cleaner imports.
"""
from app.ml.utils.embeddings import get_embedding, get_embeddings_batch
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Wrapper class for dependency-injected embedding operations."""
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.dim = settings.EMBEDDING_DIM
    
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        return get_embedding(text)
    
    async def embed_batch(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return get_embeddings_batch(texts, batch_size=batch_size)
