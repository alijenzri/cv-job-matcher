"""
RAG Service: thin wrapper for the RAG system.
"""
from app.core.rag_system import RAGSystem


class RAGService:
    def __init__(self, rag_system: RAGSystem):
        self.rag_system = rag_system

    async def get_insights(self, query: str, use_hybrid: bool = False) -> dict:
        """Query the RAG system for candidate insights."""
        return await self.rag_system.query(query, use_hybrid=use_hybrid)
