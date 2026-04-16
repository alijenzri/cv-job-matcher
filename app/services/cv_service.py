"""
CV Service: handles upload flow, background dispatch, and status lookup.
"""
from app.core.cv_processor import CVProcessor
from app.database.vector_db import VectorDB
from app.ml.utils.embeddings import get_embedding
from app.config import settings
import uuid
import os
import shutil
import logging

logger = logging.getLogger(__name__)


class CVService:
    def __init__(self, cv_processor: CVProcessor, vector_db: VectorDB):
        self.cv_processor = cv_processor
        self.vector_db = vector_db

    async def upload_cv(self, file) -> dict:
        """
        Synchronous upload path (for simple deployments without Celery).
        Parses, embeds, and stores the CV within the request cycle.
        """
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        processed_data = self.cv_processor.process(file_path)
        text = processed_data["text"]

        structured_data = self.cv_processor.extract_structured_data(text)

        embedding = get_embedding(text)

        cv_id = str(uuid.uuid4())
        
        skills_raw = structured_data.get("skills", [])
        skills_str = ", ".join(skills_raw) if isinstance(skills_raw, list) and skills_raw else "None listed"

        metadata = {
            "source": file_path,
            "filename": file.filename,
            "name": structured_data.get("name", "Unknown"),
            "email": structured_data.get("email", ""),
            "skills": skills_str,
            "summary": structured_data.get("summary", "")[:200]
        }

        self.vector_db.add_embeddings(
            ids=[cv_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text]
        )

        return {
            "id": cv_id,
            "filename": file.filename,
            "parsed_data": structured_data
        }

    def dispatch_async(self, file_path: str, filename: str) -> str:
        """
        Dispatch CV processing to Celery background worker.
        Creates a 'pending' record immediately and returns the CV ID.
        """
        cv_id = str(uuid.uuid4())

        # Create pending record for status tracking
        self.vector_db.create_pending_cv(cv_id, filename)

        # Dispatch to Celery
        from app.core.tasks import process_cv_task
        process_cv_task.delay(file_path, filename, cv_id)

        logger.info(f"Dispatched async processing for {filename} → CV ID: {cv_id}")
        return cv_id

    async def process_and_store_cv_background(self, file_path: str, filename: str):
        """
        FastAPI BackgroundTasks fallback (no Celery required).
        Runs in-process on a background thread.
        """
        cv_id = str(uuid.uuid4())
        try:
            processed_data = self.cv_processor.process(file_path)
            text = processed_data["text"]

            structured_data = self.cv_processor.extract_structured_data(text)

            embedding = get_embedding(text)

            skills_raw = structured_data.get("skills", [])
            skills_str = ", ".join(skills_raw) if isinstance(skills_raw, list) and skills_raw else "None listed"

            metadata = {
                "source": file_path,
                "filename": filename,
                "name": structured_data.get("name", "Unknown"),
                "email": structured_data.get("email", ""),
                "skills": skills_str,
                "summary": structured_data.get("summary", "")[:200]
            }

            self.vector_db.add_embeddings(
                ids=[cv_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[text]
            )
            logger.info(f"✅ Background processed {filename}. ID: {cv_id}")
        except Exception as e:
            logger.error(f"❌ Background processing failed for {filename}: {e}")
        finally:
            # Cleanup temp file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass

    def get_status(self, cv_id: str) -> dict:
        """Get the processing status of a CV by its ID."""
        result = self.vector_db.get_cv_status(cv_id)
        if not result:
            return {"id": cv_id, "status": "not_found"}
        return result
