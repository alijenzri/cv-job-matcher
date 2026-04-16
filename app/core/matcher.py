"""
Cross-Encoder based re-ranking module.
Supports single match and high-throughput batched inference.
"""
from sentence_transformers import CrossEncoder
from app.config import settings
from app.core.llm import LLMService
import logging
import json

logger = logging.getLogger(__name__)


class Matcher:
    def __init__(self, llm_service: LLMService = None):
        logger.info(f"Loading Cross-Encoder: {settings.CROSS_ENCODER_MODEL}")
        self.cross_encoder = CrossEncoder(settings.CROSS_ENCODER_MODEL)
        self.llm_service = llm_service or LLMService()
        logger.info("Cross-Encoder and Intelligence Layer initialized.")

    async def match(self, cv_text: str, job_description: str) -> dict:
        """
        Match a single CV against a Job Description.
        Returns relevance score + structured analytical intelligence.
        """
        # 1. Fast Scoring (Cross-Encoder)
        scores = self.cross_encoder.predict([(cv_text, job_description)])
        
        def normalize_logit(logit):
            normalized = ((logit + 12) / 20) * 100
            return max(0.0, min(100.0, normalized))
            
        prob = normalize_logit(float(scores[0]))
        normalized_score = round(prob, 2)

        # 2. Deep Intelligence (LLM)
        intelligence = await self._generate_intelligence(cv_text, job_description)

        return {
            "score": normalized_score,
            "details": f"Cross-Encoder relevance ({settings.CROSS_ENCODER_MODEL}) with LLM Reasoning",
            **intelligence
        }

    async def _generate_intelligence(self, cv_text: str, job_text: str) -> dict:
        """
        Generates structured intelligence about the match using LLM.
        """
        prompt = f"""
        Analyze the match between this CV and Job Description.
        
        [CV TEXT]
        {cv_text[:3000]}
        
        [JOB DESCRIPTION]
        {job_text[:3000]}
        
        Return a JSON object with:
        - "reasoning": A 2-sentence explanation of why this candidate is or isn't a fit.
        - "matching_skills": List of top 5 specific skills that match.
        - "missing_skills": List of critical requirements missing from the CV.
        - "experience_delta": Brief comment on the years of experience vs requirements.
        - "verdict": One word (Strong Match, Good Match, Weak Match, No Fit).
        """

        try:
            response_json = self.llm_service.generate_structured_json(
                prompt, 
                system_prompt="You are a senior technical recruiter analyzing candidate suitability."
            )
            
            # Robustly locate the JSON bounds
            start_idx = response_json.find('{')
            end_idx = response_json.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                clean_json = response_json[start_idx:end_idx + 1]
                return json.loads(clean_json)
            else:
                raise ValueError("No JSON object found in response.")
        except Exception as e:
            logger.error(f"Failed to generate match intelligence: {e}")
            return {
                "reasoning": "Intelligence generation failed.",
                "matching_skills": [],
                "missing_skills": [],
                "experience_delta": "N/A",
                "verdict": "Check Score"
            }

    async def match_batch(
        self, cv_texts: list[str], job_description: str, batch_size: int = None
    ) -> list[dict]:
        if not cv_texts:
            return []

        if batch_size is None:
            batch_size = settings.RERANK_BATCH_SIZE

        # Pass full strings mapping
        pairs = [(cv, job_description) for cv in cv_texts]

        logger.info(f"Batch re-ranking {len(pairs)} candidates (batch_size={batch_size})")
        
        raw_scores = self.cross_encoder.predict(pairs, batch_size=batch_size)

        def normalize_logit(logit):
            normalized = ((logit + 12) / 20) * 100
            return max(0.0, min(100.0, normalized))

        results = []
        for i, score in enumerate(raw_scores):
            prob = normalize_logit(float(score))
            results.append({
                "score": round(prob, 2),
                "details": f"Batch Cross-Encoder relevance (rank #{i+1})"
            })

        return results

    async def enrich_candidates(
        self, candidates: list[dict], cv_texts: list[str], job_text: str
    ) -> list[dict]:
        """
        Enrich a list of candidates with deep intelligence layers.
        Only call this for the top-N candidates to manage latency and cost.
        """
        logger.info(f"Enriching {len(candidates)} top candidates with intelligence")
        for i, candidate in enumerate(candidates):
            # Assuming candidates and cv_texts are aligned or candidate has ref
            # In our MatchingService flow, they are aligned in the result list
            intel = await self._generate_intelligence(cv_texts[i], job_text)
            candidate.update(intel)
        
    async def match_batch_jobs(
        self, cv_text: str, job_texts: list[str], batch_size: int = None
    ) -> list[dict]:
        """
        Batch-match a single CV against multiple Job Descriptions.
        Returns base scores.
        """
        if not job_texts:
            return []
            
        if batch_size is None:
            batch_size = settings.RERANK_BATCH_SIZE

        # Pass full strings. Tokenizer handles token truncation implicitly.
        pairs = [(cv_text, job) for job in job_texts]

        logger.info(f"Batch re-ranking {len(pairs)} jobs (batch_size={batch_size})")

        raw_scores = self.cross_encoder.predict(pairs, batch_size=batch_size)

        # MS MARCO models output uncalibrated logits, typically between -12 and +8
        def normalize_logit(logit):
            # Linearly map a logit of -12 to 0% and +8 to 100%
            normalized = ((logit + 12) / 20) * 100
            return max(0.0, min(100.0, normalized))

        results = []
        for i, score in enumerate(raw_scores):
            prob = normalize_logit(float(score))
            results.append({
                "score": round(prob, 2)
            })

        return results

    async def enrich_jobs(
        self, jobs: list[dict], cv_text: str, top_k: int = 5
    ) -> list[dict]:
        """
        Enrich a list of job match dictionaries (containing 'description' keys) with LLM intelligence.
        """
        logger.info(f"Enriching top {min(len(jobs), top_k)} jobs with intelligence")
        
        for i, job_dict in enumerate(jobs):
            if i >= top_k:
                # Provide dummy enrichment for jobs outside the top K, to save LLM tokens
                intel = {
                    "reasoning": "Not enriched (outside top 5).",
                    "matching_skills": [],
                    "missing_skills": [],
                    "experience_delta": "N/A",
                    "verdict": "Unchecked",
                    "summary": "Not enriched"
                }
            else:
                job_desc = job_dict.get("description", "")
                intel = await self._generate_intelligence(cv_text, job_desc)
                intel["summary"] = intel.get("reasoning", "")
                
            job_dict.update(intel)

        return jobs

