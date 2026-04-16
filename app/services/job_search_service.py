"""
Job Search Service: end-to-end pipeline that:
1. Parses and embeds a CV
2. Searches LinkedIn for jobs matching the given job title
3. Scores each job against the CV using Cross-Encoder
4. Returns a ranked list of up to 50 job offers with match scores
"""
import os
import uuid
import asyncio
import logging

from app.core.cv_processor import CVProcessor
from app.core.matcher import Matcher
from app.ml.utils.embeddings import get_embedding
from app.scrapers.linkedin_search_scraper import LinkedInSearchScraper
from app.scrapers.linkedin_scraper import LinkedInScraper
from app.config import settings

logger = logging.getLogger(__name__)


class JobSearchService:
    def __init__(self, cv_processor: CVProcessor, matcher: Matcher):
        self.cv_processor = cv_processor
        self.matcher = matcher
        self.search_scraper = LinkedInSearchScraper()
        self.detail_scraper = LinkedInScraper()

    async def search_and_rank(
        self,
        cv_file_path: str,
        cv_filename: str,
        job_title: str,
        location: str = "",
        max_results: int = 50,
    ) -> dict:
        """
        Full pipeline:
        1. Parse CV → extract text
        2. Search LinkedIn for `job_title` → collect up to max_results listing URLs
        3. Scrape each job listing for full description
        4. Score each job against the CV with Cross-Encoder
        5. Sort by score descending and return top results

        Returns:
            dict with cv_summary and ranked list of job offers
        """
        # ── Step 1: Parse CV ─────────────────────────────────────────
        logger.info(f"[job-search] Processing CV: {cv_filename}")
        try:
            processed = self.cv_processor.process(cv_file_path)
            cv_text = processed["text"]
            structured = self.cv_processor.extract_structured_data(cv_text)
        except Exception as e:
            raise RuntimeError(f"Failed to parse CV: {e}")
        finally:
            # cleanup temp file
            try:
                if os.path.exists(cv_file_path):
                    os.remove(cv_file_path)
            except OSError:
                pass

        # ── Step 2: Search LinkedIn ───────────────────────────────────
        logger.info(f"[job-search] Searching LinkedIn for: '{job_title}' in '{location or 'Any'}'")
        search_results = await self.search_scraper.search_jobs(
            job_title=job_title,
            location=location,
            max_results=max_results,
        )

        if not search_results:
            logger.warning("[job-search] No job listings found on LinkedIn.")
            return {
                "cv_summary": self._build_cv_summary(structured, cv_filename),
                "job_title_searched": job_title,
                "location": location,
                "total_found": 0,
                "results": [],
            }

        # ── Step 3: Scrape each job's full description (concurrently) ──
        logger.info(f"[job-search] Scraping {len(search_results)} job listings for full details...")
        detail_tasks = [
            self._safe_scrape_details(job)
            for job in search_results
        ]
        detailed_jobs = await asyncio.gather(*detail_tasks)

        # Filter jobs that have a description
        valid_jobs = [j for j in detailed_jobs if j.get("description")]
        fallback_jobs = [j for j in detailed_jobs if not j.get("description")]

        logger.info(f"[job-search] {len(valid_jobs)} jobs have descriptions, {len(fallback_jobs)} used search-page only")

        # Jobs without descriptions: use title+company as minimal text
        for j in fallback_jobs:
            j["description"] = f"{j.get('title', '')} at {j.get('company', '')}. {j.get('location', '')}"

        all_jobs = valid_jobs + fallback_jobs

        # ── Step 4: Score all jobs against CV ────────────────────────
        logger.info(f"[job-search] Scoring {len(all_jobs)} jobs against CV...")
        job_texts = [
            f"{j.get('title', '')} at {j.get('company', '')}\n{j.get('description', '')}"
            for j in all_jobs
        ]

        scores = await self.matcher.match_batch(job_texts, cv_text)

        # ── Step 5: Merge scores + sort ──────────────────────────────
        results = []
        for i, job in enumerate(all_jobs):
            score_data = scores[i] if i < len(scores) else {"score": 0.0, "details": ""}
            results.append({
                "rank": 0,  # filled after sort
                "score": score_data["score"],
                "title": job.get("title", "Unknown"),
                "company": job.get("company", "Unknown"),
                "location": job.get("location", ""),
                "url": job.get("url", ""),
                "platform": job.get("platform", "linkedin"),
                "salary": job.get("salary", "Not listed"),
                "job_type": job.get("job_type", "Not listed"),
                "description_preview": (job.get("description", "")[:300] + "...") if job.get("description") else "",
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(results):
            r["rank"] = i + 1

        top_results = results[:max_results]

        logger.info(f"[job-search] ✅ Returning {len(top_results)} ranked job offers")

        return {
            "cv_summary": self._build_cv_summary(structured, cv_filename),
            "job_title_searched": job_title,
            "location": location,
            "total_found": len(top_results),
            "results": top_results,
        }

    async def _safe_scrape_details(self, job: dict) -> dict:
        """Scrape full job details; on failure return the shallow search result."""
        url = job.get("url", "")
        if not url:
            return job
        try:
            details = await self.detail_scraper.scrape(url)
            if details.get("error") or not details.get("description"):
                return job  # fallback to search-page data
            # Merge details into job dict (details wins except url)
            return {
                "title": details.get("title") or job.get("title", ""),
                "company": details.get("company") or job.get("company", ""),
                "location": details.get("location") or job.get("location", ""),
                "description": details.get("description", ""),
                "salary": details.get("salary", "Not listed"),
                "job_type": details.get("job_type", "Not listed"),
                "url": url,
                "platform": "linkedin",
            }
        except Exception as e:
            logger.debug(f"[job-search] Failed to scrape details for {url}: {e}")
            return job

    def _build_cv_summary(self, structured: dict, filename: str) -> dict:
        return {
            "filename": filename,
            "name": structured.get("name", "Unknown"),
            "email": structured.get("email", ""),
            "skills": structured.get("skills", [])[:10],
            "summary": structured.get("summary", "")[:200],
        }
