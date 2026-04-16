from app.models.job import Job
from app.database.vector_db import VectorDB
from app.ml.utils.embeddings import get_embedding
import uuid

class JobService:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db

    async def create_job(self, job_data: dict):
        # 1. Prepare data
        job_id = str(uuid.uuid4())
        title = job_data.get("title", "Unknown Job")
        description = job_data.get("description", "")
        full_text = f"{title}\n{description}"
        
        # 2. Embed
        embedding = get_embedding(full_text)
        
        # 3. Store in VectorDB (Job Collection)
        metadata = {
            "title": title,
            "company": job_data.get("company", ""),
        }
        
        self.vector_db.add_job_embeddings(
            ids=[job_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[full_text]
        )
        
        # 4. Return Job Model (Assuming we might want more complex object later)
        # Verify if Job model accepts id. app/models/job.py not viewed, assume flexible or dict for now if needed.
        # But schemas.py has JobDescriptionResponse with 'id'.
        
        return {
            "id": job_id,
            "title": title,
            "description": description,
            "company": job_data.get("company", "")
        }
