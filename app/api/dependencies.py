"""
FastAPI dependency injection providers.
Uses lru_cache for singleton services (models loaded once).
"""
from fastapi import Header, HTTPException
from app.services.cv_service import CVService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.rag_service import RAGService
from app.core.cv_processor import CVProcessor
from app.core.matcher import Matcher
from app.core.llm import LLMService
from app.core.rag_system import RAGSystem
from app.database.vector_db import VectorDB
from app.rag.retriever import HyDERetriever
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@lru_cache()
def get_vector_db() -> VectorDB:
    logger.info("Initializing VectorDB singleton...")
    return VectorDB()


@lru_cache()
def get_llm_service() -> LLMService:
    logger.info("Initializing LLMService singleton...")
    return LLMService()


@lru_cache()
def get_matcher() -> Matcher:
    logger.info("Initializing Matcher singleton (Cross-Encoder)...")
    return Matcher()


def get_cv_service() -> CVService:
    return CVService(CVProcessor(), get_vector_db())


def get_job_service() -> JobService:
    return JobService(get_vector_db())


def get_matching_service() -> MatchingService:
    return MatchingService(
        get_matcher(),
        get_vector_db(),
        HyDERetriever(get_vector_db(), get_llm_service()),
        CVProcessor()
    )


def get_rag_service() -> RAGService:
    return RAGService(RAGSystem())


def get_scraping_service():
    from app.services.scraping_service import ScrapingService
    return ScrapingService(get_vector_db())


def get_job_search_service():
    from app.services.job_search_service import JobSearchService
    return JobSearchService(CVProcessor(), get_matcher())
