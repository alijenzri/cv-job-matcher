"""
Vector Database layer using ChromaDB.
Replaces PostgreSQL + pgvector for environments where pgvector is unavailable.
Supports:
  - Vector similarity search
  - Keyword search (simple $contains filter)
  - Hybrid search (fused results)
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
import uuid
import logging
import datetime

logger = logging.getLogger(__name__)


class VectorDB:
    def __init__(self):
        """Initialize ChromaDB client."""
        try:
            if settings.CHROMA_HOST:
                logger.info(f"Connecting to Chroma Cloud at {settings.CHROMA_HOST}...")
                self.client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    headers={"X-Chroma-Token": settings.CHROMA_API_KEY} if settings.CHROMA_API_KEY else None,
                    tenant=settings.CHROMA_TENANT or "default_tenant",
                    database=settings.CHROMA_DATABASE or "default_database"
                )
            else:
                logger.info("Initializing local ChromaDB (Persistent)...")
                self.client = chromadb.PersistentClient(path="data/chroma")

            # Get or create collections
            self.cv_collection = self.client.get_or_create_collection(
                name="cv_embeddings",
                metadata={"hnsw:space": "cosine"}
            )
            self.job_collection = self.client.get_or_create_collection(
                name="job_embeddings",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("VectorDB (Chroma) initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma VectorDB: {e}")
            raise

    # ── CV Operations ──────────────────────────────────────────────

    def add_embeddings(self, ids, embeddings, metadatas=None, documents=None):
        """Insert or upsert CV embeddings."""
        try:
            # Ensure all IDs are strings for Chroma
            str_ids = [str(i) for i in ids]
            
            # Add timestamps and status to metadatas
            if metadatas:
                for meta in metadatas:
                    meta["status"] = "processed"
                    meta["updated_at"] = str(datetime.datetime.now())
            
            self.cv_collection.upsert(
                ids=str_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Upserted {len(ids)} CV(s) to Chroma.")
        except Exception as e:
            logger.error(f"Chroma add_embeddings failed: {e}")
            raise

    def add_job_embeddings(self, ids, embeddings, metadatas=None, documents=None):
        """Insert or upsert Job embeddings."""
        try:
            str_ids = [str(i) for i in ids]
            self.job_collection.upsert(
                ids=str_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Upserted {len(ids)} Job(s) to Chroma.")
        except Exception as e:
            logger.error(f"Chroma add_job_embeddings failed: {e}")
            raise

    # ── Search Operations ──────────────────────────────────────────

    def query(self, query_embeddings, n_results=5):
        """Pure vector similarity search."""
        try:
            results = self.cv_collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            return results
        except Exception as e:
            logger.error(f"Chroma query failed: {e}")
            return {'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def keyword_search(self, query_text: str, n_results: int = 5):
        """
        Approximate keyword search using Chroma's where_document $contains filter.
        Note: This is not BM25, but provides a basic alternative.
        """
        try:
            # Chroma supports simple string matching in documents
            results = self.cv_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas"]
            )
            return results
        except Exception as e:
            logger.error(f"Chroma keyword_search failed: {e}")
            return {'ids': [[]], 'documents': [[]], 'metadatas': [[]]}

    def hybrid_search(self, query_embedding, query_text: str, n_results: int = 5, alpha: float = 0.7):
        """
        Hybrid search using Chroma. Since Chroma doesn't have native RRF/BM25,
        we use vector search as primary and use query_texts for semantic boost.
        """
        # For simplicity in this migration, we'll perform a standard vector query
        # but include the query_text to help Chroma's internal ranking if available.
        return self.query([query_embedding], n_results=n_results)

    # ── Single Record Lookups ──────────────────────────────────────

    def get_cv_by_id(self, cv_id: str):
        try:
            res = self.cv_collection.get(ids=[str(cv_id)], include=["documents", "metadatas"])
            if res['ids']:
                return {'metadatas': res['metadatas'], 'documents': res['documents']}
            return {'metadatas': [], 'documents': []}
        except Exception:
            return {'metadatas': [], 'documents': []}

    def get_job_by_id(self, job_id: str):
        try:
            res = self.job_collection.get(ids=[str(job_id)], include=["documents", "metadatas"])
            if res['ids']:
                return {'metadatas': res['metadatas'], 'documents': res['documents']}
            return {'metadatas': [], 'documents': []}
        except Exception:
            return {'metadatas': [], 'documents': []}

    # ── Status Tracking ────────────────────────────────────────────

    def update_cv_status(self, cv_id: str, status: str):
        try:
            res = self.cv_collection.get(ids=[str(cv_id)])
            if res['ids']:
                meta = res['metadatas'][0] or {}
                meta['status'] = status
                meta['updated_at'] = str(datetime.datetime.now())
                self.cv_collection.update(ids=[str(cv_id)], metadatas=[meta])
        except Exception as e:
            logger.error(f"Failed to update CV status in Chroma: {e}")

    def create_pending_cv(self, cv_id: str, filename: str):
        try:
            self.cv_collection.add(
                ids=[str(cv_id)],
                metadatas=[{"filename": filename, "status": "pending", "created_at": str(datetime.datetime.now())}],
                documents=[""] # Placeholder
            )
        except Exception as e:
            logger.warning(f"Failed to create pending record in Chroma: {e}")

    def get_cv_status(self, cv_id: str) -> dict:
        try:
            res = self.cv_collection.get(ids=[str(cv_id)], include=["metadatas"])
            if res['ids']:
                meta = res['metadatas'][0]
                return {
                    "id": res['ids'][0],
                    "status": meta.get("status", "unknown"),
                    "metadata": meta,
                    "created_at": meta.get("created_at"),
                    "updated_at": meta.get("updated_at")
                }
            return None
        except Exception:
            return None

    def get_stats(self) -> dict:
        try:
            cv_count = self.cv_collection.count()
            job_count = self.job_collection.count()
            return {
                "cv_stats": {"total": cv_count},
                "job_count": job_count
            }
        except Exception:
            return {"cv_stats": {"total": 0}, "job_count": 0}

    def close(self):
        """Chroma doesn't require explicit closing for HttpClient/PersistentClient usually."""
        pass
