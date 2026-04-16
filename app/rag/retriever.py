"""
HyDE (Hypothetical Document Embeddings) Retriever.
Generates a hypothetical ideal candidate profile, embeds it,
and uses that embedding for vector search — improving recall for
queries that are phrased as job descriptions rather than candidate profiles.
Supports both pure vector and hybrid search modes.
"""
from app.core.llm import LLMService
from app.database.vector_db import VectorDB
from app.ml.utils.embeddings import get_embedding
import logging

logger = logging.getLogger(__name__)


class HyDERetriever:
    def __init__(self, vector_db: VectorDB, llm_service: LLMService):
        self.vector_db = vector_db
        self.llm_service = llm_service

    def retrieve(self, query: str, n_results: int = 5, use_hybrid: bool = False) -> dict:
        """
        Retrieve candidates using HyDE.

        Args:
            query: The job description or search query.
            n_results: Number of results to return.
            use_hybrid: If True, uses hybrid (vector + keyword) search.
        """
        # 1. Generate hypothetical ideal candidate profile
        logger.info(f"HyDE: Generating hypothetical answer for query ({len(query)} chars)")
        hypothetical_answer = self.llm_service.generate_hypothetical_answer(query)

        if hypothetical_answer:
            text_to_embed = hypothetical_answer
            logger.info(f"HyDE: Using hypothetical answer ({len(hypothetical_answer)} chars)")
        else:
            text_to_embed = query
            logger.warning("HyDE: LLM generation failed, falling back to raw query")

        # 2. Embed the hypothetical document
        embedding = get_embedding(text_to_embed)

        # 3. Search
        if use_hybrid:
            results = self.vector_db.hybrid_search(
                query_embedding=embedding,
                query_text=query,
                n_results=n_results
            )
        else:
            results = self.vector_db.query(
                query_embeddings=[embedding],
                n_results=n_results
            )

        logger.info(f"HyDE: Retrieved {len(results.get('ids', [[]])[0])} results")
        return results
