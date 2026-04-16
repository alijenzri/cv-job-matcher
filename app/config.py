from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    SECRET_KEY: str = "change_me_in_production"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cv_matcher"
    
    # AI/LLM
    GOOGLE_API_KEY: Optional[str] = None
    HUGGINGFACE_API_TOKEN: Optional[str] = None
    
    # Redis / Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Upload
    UPLOAD_DIR: str = "data/uploads"
    MAX_CV_SIZE_MB: int = 10
    
    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    
    # Cross-Encoder (Re-ranking)
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_BATCH_SIZE: int = 32
    
    # Scraping
    LINKEDIN_USERNAME: Optional[str] = None
    LINKEDIN_PASSWORD: Optional[str] = None

    # Vector DB (Chroma Cloud)
    CHROMA_HOST: Optional[str] = None
    CHROMA_API_KEY: Optional[str] = None
    CHROMA_TENANT: Optional[str] = None
    CHROMA_DATABASE: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
