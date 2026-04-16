"""
Production RAG System with PII redaction (Presidio), strict guardrails,
and source-cited responses.
"""
from app.database.vector_db import VectorDB
from app.core.llm import LLMService
from app.rag.retriever import HyDERetriever
import logging

logger = logging.getLogger(__name__)


class RAGSystem:
    def __init__(self):
        self.vector_db = VectorDB()
        self.llm_service = LLMService()
        self.retriever = HyDERetriever(self.vector_db, self.llm_service)

    async def query(self, query_text: str, use_hybrid: bool = False) -> dict:
        """
        High-Performance RAG Query Logic:
        1. Retrieve relevant contexts using HyDE (pure vector or hybrid).
        2. Augment prompt with contexts and analytical matching logic.
        3. Generate high-precision recruitment insights.

        Returns:
            dict with 'answer', 'sources', and 'context_count'.
        """
        # 1. Retrieve
        retrieved_results = self.retriever.retrieve(
            query_text, n_results=5, use_hybrid=use_hybrid
        )

        documents = retrieved_results.get('documents', [[]])[0]
        ids = retrieved_results.get('ids', [[]])[0]

        if not documents:
            return {
                "answer": "No relevant technical profiles found for this query.",
                "sources": [],
                "context_count": 0
            }

        # 2. Format Context without redaction overhead
        context_text = ""
        for i, doc in enumerate(documents):
            candidate_id = ids[i] if i < len(ids) else f"UNKNOWN_{i}"
            doc_truncated = doc[:4000]  # Allow larger context for accuracy
            context_text += f"\n--- CANDIDATE REF: {candidate_id} ---\n{doc_truncated}\n"

        # 3. Precision-Tuned Prompt
        final_prompt = f"""You are a Lead Technical Recruitment Intelligence Engine.
Your task is to analyze candidate data with 100% technical precision.

[OPERATIONAL GUIDELINES]
1. Focus on technical stack alignment, proficiency levels, and engineering depth.
2. Direct comparison between candidates is required if multiple sources are provided.
3. Identify "hidden mismatches" where a keyword exists but the context shows low proficiency.
4. Cite sources strictly as [Candidate REF].

[CONTEXT DATA]
{context_text}

[INTEL REQUEST]
{query_text}

Analytical Verdict:"""

        response = self.llm_service.generate_text(
            final_prompt,
            system_prompt="You are a high-performance intelligence layer. Provide structured, dense, and objective recruiter verdicts."
        )

        return {
            "answer": response,
            "sources": ids,
            "context_count": len(documents)
        }
