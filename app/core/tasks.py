"""
Celery task definitions for background processing.
All heavy I/O and ML inference runs here, outside the API request cycle.
"""
from app.main import celery_app
from app.core.cv_processor import CVProcessor
from app.database.vector_db import VectorDB
from app.ml.utils.embeddings import get_embedding
import uuid
import logging
import os

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_cv_task(self, file_path: str, filename: str, cv_id: str):
    """
    Celery task: Parse a CV, extract structured data, embed it, and store in pgvector.
    Automatically retries up to 3 times on failure.
    """
    vector_db = VectorDB()
    cv_processor = CVProcessor()

    try:
        logger.info(f"[Task {self.request.id}] Processing CV: {filename} (ID: {cv_id})")

        # 1. Parse Document (unstructured.io)
        processed_data = cv_processor.process(file_path)
        text = processed_data["text"]
        logger.info(f"[Task {self.request.id}] Parsed {processed_data['metadata']['chunk_count']} chunks")

        # 2. Extract Structured Metadata (LLM)
        structured_data = cv_processor.extract_structured_data(text)

        # 3. Generate Embedding
        embedding = get_embedding(text)

        # 4. Store in pgvector
        metadata = {
            "source": file_path,
            "filename": filename,
            "name": structured_data.get("name", "Unknown"),
            "email": structured_data.get("email", ""),
            "skills": structured_data.get("skills", []),
            "summary": structured_data.get("summary", "")[:200],
        }

        vector_db.add_embeddings(
            ids=[cv_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text]
        )

        logger.info(f"✅ [Task {self.request.id}] Successfully processed {filename}. ID: {cv_id}")
        return {"status": "processed", "cv_id": cv_id, "filename": filename}

    except Exception as exc:
        logger.error(f"❌ [Task {self.request.id}] Failed to process {filename}: {exc}")
        # Update status to 'failed' in DB
        try:
            vector_db.update_cv_status(cv_id, "failed")
        except Exception:
            pass
        # Retry with exponential backoff
        raise self.retry(exc=exc)
    finally:
        # Cleanup temp file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
        vector_db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def scrape_job_task(self, url: str):
    """
    Celery task: Scrape a job posting asynchronously using ScrapingService.
    Playwright is fully async, so we use asyncio.run().
    """
    import asyncio
    from app.services.scraping_service import ScrapingService
    from app.database.vector_db import VectorDB
    
    vector_db = VectorDB()
    try:
        logger.info(f"[Task {self.request.id}] Scraping Job URL: {url}")
        
        scraping_service = ScrapingService(vector_db)
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.warning("Event loop is already running, creating a new thread to run async task")
            # In celery prefork, we might need a distinct loop, but asyncio.run is safe if no loop is running.
            result = asyncio.run(scraping_service.scrape_and_store_job(url))
        else:
            result = asyncio.run(scraping_service.scrape_and_store_job(url))
        
        if result["status"] == "success":
            logger.info(f"✅ [Task {self.request.id}] Successfully scraped {url}.")
            return result
        else:
            raise Exception(result.get("error", "Unknown error"))
    except Exception as exc:
        logger.error(f"❌ [Task {self.request.id}] Failed to scrape {url}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)
    finally:
        vector_db.close()
