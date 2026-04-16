"""
Matching Service: orchestrates candidate search and re-ranking.
Supports both pure vector search and hybrid (vector + keyword) search.
"""
from app.core.matcher import Matcher
from app.database.vector_db import VectorDB
from app.rag.retriever import HyDERetriever
from app.ml.utils.embeddings import get_embedding
from app.core.cv_processor import CVProcessor
import logging

logger = logging.getLogger(__name__)


class MatchingService:
    def __init__(self, matcher: Matcher, vector_db: VectorDB, hyde_retriever: HyDERetriever, cv_processor: CVProcessor = None):
        self.matcher = matcher
        self.vector_db = vector_db
        self.hyde_retriever = hyde_retriever
        self.cv_processor = cv_processor or CVProcessor()

    async def create_match(self, cv_id: str, job_id: str) -> dict:
        """
        Score a specific CV against a specific Job (1:1 matching).
        """
        cv_data = self.vector_db.get_cv_by_id(cv_id)
        job_data = self.vector_db.get_job_by_id(job_id)

        if not cv_data['documents'] or not job_data['documents']:
            raise ValueError("CV or Job not found in database")

        cv_text = cv_data['documents'][0]
        job_text = job_data['documents'][0]

        result = await self.matcher.match(cv_text, job_text)

        return {
            "cv_id": cv_id,
            "job_id": job_id,
            "score": result['score'],
            "summary": result.get('reasoning', result['details']),
            "matching_skills": result.get('matching_skills', []),
            "missing_skills": result.get('missing_skills', []),
            "experience_delta": result.get('experience_delta'),
            "verdict": result.get('verdict'),
            "reasoning": result.get('reasoning')
        }

    async def match_stateless_batch(self, cv_file_path: str, jobs_data: list[dict]) -> dict:
        """
        Score an uploaded CV against an array of job description dicts (Adzuna format).
        Does NOT persist to database.
        """
        # 1. Parse CV
        processed_data = self.cv_processor.process(cv_file_path)
        cv_text = processed_data["text"]

        # 2. Extract structured data (optional, but requested for V2)
        structured_cv = self.cv_processor.extract_structured_data(cv_text)

        if not jobs_data:
            return {
                "parsed_cv": structured_cv,
                "total_jobs_processed": 0,
                "results": []
            }

        # 3. Extract descriptions and build scoring batch
        job_texts = []
        for job in jobs_data:
            # Try adzuna schema standard keys first
            desc = job.get("description") or job.get("text") or str(job)
            job_texts.append(desc)

        # 4. Batch Match
        raw_scores = await self.matcher.match_batch_jobs(cv_text, job_texts)

        # 5. Build results objects
        matched_jobs = []
        for i, job in enumerate(jobs_data):
            company = job.get("company", {})
            company_name = company.get("display_name", company) if isinstance(company, dict) else str(company)
            
            matched_jobs.append({
                "score": raw_scores[i]["score"],
                "title": job.get("title", "Unknown"),
                "company": company_name if company_name else "Unknown",
                "description": job_texts[i],
                "description_preview": job_texts[i][:200] + "..." if len(job_texts[i]) > 200 else job_texts[i],
            })

        # 6. Sort dynamically by score desc
        matched_jobs.sort(key=lambda x: x["score"], reverse=True)

        # 7. Enrich top candidates with LLM
        enriched_jobs = await self.matcher.enrich_jobs(matched_jobs, cv_text, top_k=5)
        
        # Cleanup full description so payload is not massive
        for job in enriched_jobs:
            job.pop("description", None)

        return {
            "parsed_cv": structured_cv,
            "total_jobs_processed": len(jobs_data),
            "results": enriched_jobs
        }

    async def search_candidates(self, job_id: str, top_k: int = 5) -> list[dict]:
        """
        Search for top candidates using HyDE retrieval + Cross-Encoder re-ranking.
        Enhanced with deep intelligence layer for top results.
        """
        # 1. Get Job Description
        job_data = self.vector_db.get_job_by_id(job_id)
        if not job_data['documents']:
            raise ValueError("Job not found")

        job_text = job_data['documents'][0]

        # 2. Retrieve candidates via HyDE
        retrieval_count = min(top_k * 3, 50)
        retrieved_results = self.hyde_retriever.retrieve(
            query=job_text, n_results=retrieval_count
        )

        ids = retrieved_results['ids'][0]
        documents = retrieved_results['documents'][0]

        if not documents:
            logger.warning(f"No candidates found for job {job_id}")
            return []

        # 3. Re-rank with Cross-Encoder
        batch_scores = await self.matcher.match_batch(documents, job_text)

        # 4. Filter and Sort
        candidates = []
        for i, score_data in enumerate(batch_scores):
            candidates.append({
                "cv_id": ids[i],
                "cv_text": documents[i],  # Keep for enrichment
                "score": score_data['score'],
                "details": score_data['details']
            })

        candidates.sort(key=lambda x: x['score'], reverse=True)
        top_candidates = candidates[:top_k]

        # 5. Enrich top candidates with Intelligence Layer
        enriched = await self.matcher.enrich_candidates(
            top_candidates, 
            [c['cv_text'] for c in top_candidates],
            job_text
        )

        # Cleanup: removes temp cv_text before returning
        for i, c in enumerate(enriched):
            c.pop('cv_text', None)
            c['rank'] = i + 1

        return enriched

    async def search_candidates_hybrid(self, job_id: str, top_k: int = 5) -> list[dict]:
        """
        Search using hybrid (vector + keyword) search for maximum recall,
        then re-rank with Cross-Encoder.
        """
        job_data = self.vector_db.get_job_by_id(job_id)
        if not job_data['documents']:
            raise ValueError("Job not found")

        job_text = job_data['documents'][0]

        # 1. Generate query embedding for hybrid search
        query_embedding = get_embedding(job_text)

        # 2. Hybrid search (vector + BM25 keyword via RRF)
        retrieval_count = min(top_k * 3, 50)
        hybrid_results = self.vector_db.hybrid_search(
            query_embedding=query_embedding,
            query_text=job_text,
            n_results=retrieval_count,
            alpha=0.7  # 70% vector, 30% keyword
        )

        ids = hybrid_results['ids'][0]
        documents = hybrid_results['documents'][0]

        if not documents:
            logger.warning(f"No candidates found for job {job_id} via hybrid search")
            return []

        # 3. Re-rank with Cross-Encoder
        batch_scores = await self.matcher.match_batch(documents, job_text)

        candidates = []
        for i, score_data in enumerate(batch_scores):
            candidates.append({
                "cv_id": ids[i],
                "cv_text": documents[i],  # Keep for enrichment
                "score": score_data['score'],
                "details": score_data['details']
            })

        candidates.sort(key=lambda x: x['score'], reverse=True)
        top_candidates = candidates[:top_k]

        # 4. Enrich top candidates with Intelligence Layer
        enriched = await self.matcher.enrich_candidates(
            top_candidates, 
            [c['cv_text'] for c in top_candidates],
            job_text
        )

        for i, c in enumerate(enriched):
            c.pop('cv_text', None)
            c['rank'] = i + 1

        return enriched
