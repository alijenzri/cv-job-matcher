"""
Scraping service: orchestrates job scraping from URLs,
stores results in VectorDB, and integrates with job creation pipeline.
"""
from app.scrapers.factory import ScraperFactory
from app.database.vector_db import VectorDB
from app.core.job_processor import JobProcessor
from app.ml.utils.embeddings import get_embedding
from app.utils.validation import validate_job_url
import uuid
import logging

logger = logging.getLogger(__name__)


class ScrapingService:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        self.job_processor = JobProcessor()

    async def scrape_and_store_job(self, url: str) -> dict:
        """
        Scrape a job URL, extract structured data, embed it, and store.

        Returns:
            dict with job_id, scraped data, and processing status.
        """
        # 1. Validate URL
        platform = validate_job_url(url)
        if not platform:
            raise ValueError(f"Unsupported or invalid job URL: {url}")

        # 2. Scrape
        logger.info(f"Scraping job from {platform}: {url}")
        scraper = ScraperFactory.get_scraper(url)
        scraped_data = await scraper.scrape(url)

        if scraped_data.get("error"):
            logger.error(f"Scrape failed: {scraped_data['error']}")
            return {"status": "failed", "error": scraped_data["error"], "url": url}

        # 3. Process & extract structured requirements
        description = scraped_data.get("description", "")
        if not description:
            return {"status": "failed", "error": "No description found", "url": url}

        processed = self.job_processor.process(description)
        full_text = f"{scraped_data.get('title', '')}\n{processed['text']}"

        # 4. Embed
        embedding = get_embedding(full_text)

        # 5. Store
        job_id = str(uuid.uuid4())
        metadata = {
            "title": scraped_data.get("title", "Unknown"),
            "company": scraped_data.get("company", "Unknown"),
            "location": scraped_data.get("location", ""),
            "salary": scraped_data.get("salary", "Not listed"),
            "job_type": scraped_data.get("job_type", "Not listed"),
            "platform": platform,
            "url": url,
        }

        self.vector_db.add_job_embeddings(
            ids=[job_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[full_text],
        )

        logger.info(f"✅ Stored scraped job: {scraped_data.get('title')} (ID: {job_id})")

        return {
            "status": "success",
            "job_id": job_id,
            "data": scraped_data,
            "metadata": metadata,
        }

    async def scrape_multiple(self, urls: list[str]) -> list[dict]:
        """Scrape multiple job URLs. Returns results for each."""
        results = []
        for url in urls:
            try:
                result = await self.scrape_and_store_job(url)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                results.append({"status": "failed", "url": url, "error": str(e)})
        return results
