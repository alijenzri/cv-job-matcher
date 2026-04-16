"""
Production API routes for CV-Job Matcher.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, status, Header, Form
from typing import List, Dict, Any
from app.api import schemas
from app.services.cv_service import CVService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.rag_service import RAGService
from app.api.dependencies import (
    get_cv_service, get_job_service, get_matching_service,
    get_rag_service, get_vector_db, get_scraping_service,
    get_job_search_service,
)
from app.database.vector_db import VectorDB
from app.services.scraping_service import ScrapingService
from app.config import settings
import os
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


# ── CV Endpoints ───────────────────────────────────────────────────

@router.post("/cv/upload", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.CVUploadResponse)
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    cv_service: CVService = Depends(get_cv_service)
):
    """
    Upload a CV for asynchronous processing.
    Returns 202 Accepted with a CV ID for status polling.
    """
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".txt"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )

    # Validate file size
    file_bytes = await file.read()
    max_bytes = settings.MAX_CV_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_CV_SIZE_MB}MB"
        )

    # Save to temp storage
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Try Celery dispatch; fallback to BackgroundTasks
    try:
        cv_id = cv_service.dispatch_async(file_path, file.filename)
        logger.info(f"CV dispatched to Celery worker: {file.filename}")
    except Exception as e:
        logger.warning(f"Celery unavailable ({e}), using BackgroundTasks fallback")
        background_tasks.add_task(cv_service.process_and_store_cv_background, file_path, file.filename)
        cv_id = "pending-bg-task"

    return schemas.CVUploadResponse(
        message="CV upload accepted for processing",
        cv_id=cv_id,
        filename=file.filename
    )


@router.get("/cv/{cv_id}/status", response_model=schemas.CVStatusResponse)
async def get_cv_status(
    cv_id: str,
    cv_service: CVService = Depends(get_cv_service)
):
    """Poll the processing status of a CV upload."""
    result = cv_service.get_status(cv_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="CV not found")
    return result


# ── Job Endpoints ──────────────────────────────────────────────────

@router.post("/job", response_model=schemas.JobDescriptionResponse)
async def create_job_description(
    job: schemas.JobDescriptionCreate,
    job_service: JobService = Depends(get_job_service)
):
    """Add a new job description."""
    return await job_service.create_job(job.dict())


# ── Matching Endpoints ─────────────────────────────────────────────

@router.post("/match", response_model=schemas.MatchResult)
async def match_cv_to_job(
    request: schemas.MatchRequest,
    matching_service: MatchingService = Depends(get_matching_service)
):
    """Score a specific CV against a specific Job Description (1:1)."""
    try:
        return await matching_service.create_match(request.cv_id, request.job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


from pydantic import Json
from typing import List, Dict, Any

@router.post("/matchV2", response_model=schemas.MatchBatchResultV2)
async def match_cv_to_job_v2(
    file: UploadFile = File(...),
    jobs_data: str = Form(..., description="JSON string array of job offers"),
    matching_service: MatchingService = Depends(get_matching_service)
):
    """
    Score a CV file against an array of job offers (e.g. from Adzuna).
    This is a stateless endpoint: no data is persisted to the database.
    """
    import json
    try:
        jobs_list = json.loads(jobs_data)
        if not isinstance(jobs_list, list):
            raise ValueError("Expected a JSON array of job offers.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid jobs_data payload: {str(e)}")

    # 1. Save temp file
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    temp_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1].lower()
    temp_path = os.path.join(upload_dir, f"matchV2_{temp_id}{file_ext}")

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # 2. Run stateless batch match
        result = await matching_service.match_stateless_batch(temp_path, jobs_list)
        return result

    except Exception as e:
        logger.error(f"MatchV2 failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.post("/job/{job_id}/candidates", response_model=List[schemas.CandidateResult])
async def search_candidates(
    job_id: str,
    request: schemas.CandidateSearchRequest = schemas.CandidateSearchRequest(),
    matching_service: MatchingService = Depends(get_matching_service)
):
    """
    Find top candidates for a job using HyDE + Cross-Encoder re-ranking.
    Supports both pure vector and hybrid (vector + keyword) search modes.
    """
    try:
        if request.mode == schemas.SearchMode.HYBRID:
            return await matching_service.search_candidates_hybrid(job_id, request.top_k)
        else:
            return await matching_service.search_candidates(job_id, request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── RAG / Insights Endpoints ──────────────────────────────────────

@router.post("/rag/query", response_model=schemas.RAGQueryResponse)
async def rag_query(
    request: schemas.RAGQueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Ask a natural-language question about candidates.
    Uses RAG with PII redaction and strict source-citation guardrails.
    """
    result = await rag_service.get_insights(request.query, use_hybrid=request.use_hybrid)
    return result


# ── Health / Admin Endpoints ───────────────────────────────────────

@router.get("/health", response_model=schemas.HealthResponse)
async def health_check(vector_db: VectorDB = Depends(get_vector_db)):
    """Health check with database stats."""
    try:
        stats = vector_db.get_stats()
        return schemas.HealthResponse(
            status="healthy",
            version="1.0.0",
            db_stats=stats
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return schemas.HealthResponse(
            status="degraded",
            version="1.0.0",
            db_stats={"error": str(e)}
        )


# ── Scraping Endpoints ────────────────────────────────────────────

@router.post("/scrape/job", response_model=schemas.ScrapeJobResponse)
async def scrape_job(
    request: schemas.ScrapeJobRequest,
    scraping_service: ScrapingService = Depends(get_scraping_service),
):
    """
    Scrape a job posting from LinkedIn, Indeed, or Glassdoor.
    Extracts structured data, generates embeddings, and stores in the vector DB.
    """
    try:
        result = await scraping_service.scrape_and_store_job(request.url)
        return schemas.ScrapeJobResponse(
            status=result["status"],
            job_id=result.get("job_id"),
            data=result.get("data"),
            error=result.get("error"),
            url=request.url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")


@router.post("/scrape/batch", response_model=List[schemas.ScrapeJobResponse])
async def batch_scrape_jobs(
    request: schemas.BatchScrapeRequest,
    scraping_service: ScrapingService = Depends(get_scraping_service),
):
    """
    Batch scrape multiple job URLs (max 20).
    Returns results for each URL individually.
    """
    results = await scraping_service.scrape_multiple(request.urls)
    return [
        schemas.ScrapeJobResponse(
            status=r["status"],
            job_id=r.get("job_id"),
            data=r.get("data"),
            error=r.get("error"),
            url=r.get("url", ""),
        )
        for r in results
    ]


# ── CV + Job Search Endpoints ────────────────────────────────────

@router.post("/cv/search-jobs", response_model=schemas.JobSearchResponse)
async def search_jobs_for_cv(
    job_title: str = Header(...),
    location: str = Header(default=""),
    max_results: int = Header(default=10),
    file: UploadFile = File(...),
    search_service=Depends(get_job_search_service)
):
    """
    Submit a CV and a job title to find matching jobs from LinkedIn.
    This performs a live search, scrapes descriptions, and ranks them by match score.
    Note: Headers are used for parameters to avoid multipart/form-data complexity with Pydantic models.
    """
    # 1. Save CV to temp file
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    temp_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1].lower()
    temp_path = os.path.join(upload_dir, f"search_{temp_id}{file_ext}")
    
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # 2. Execute pipeline
    try:
        result = await search_service.search_and_rank(
            cv_file_path=temp_path,
            cv_filename=file.filename,
            job_title=job_title,
            location=location,
            max_results=max_results
        )
        return result
    except Exception as e:
        logger.error(f"Job search failed: {e}")
        # Ensure cleanup on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

