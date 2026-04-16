from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class CVBase(BaseModel):
    filename: str


class CVResponse(CVBase):
    id: str
    parsed_data: Dict[str, Any]


class CVUploadResponse(BaseModel):
    """Response for async CV upload (202 Accepted)."""
    message: str
    cv_id: str
    filename: str


class CVStatusResponse(BaseModel):
    """Response for CV processing status check."""
    id: str
    status: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class JobDescriptionCreate(BaseModel):
    title: str
    company: str
    description: str
    requirements: Optional[List[str]] = None


class JobDescriptionResponse(JobDescriptionCreate):
    id: str


class MatchRequest(BaseModel):
    cv_id: str
    job_id: str


class MatchResult(BaseModel):
    cv_id: str
    job_id: str
    score: float
    summary: str
    missing_skills: List[str] = []
    matching_skills: List[str] = []
    experience_delta: Optional[str] = None
    reasoning: Optional[str] = None
    verdict: Optional[str] = None


class JobOfferMatchResult(BaseModel):
    score: float
    title: str = "Unknown"
    company: str = "Unknown"
    description_preview: str = ""
    summary: str
    missing_skills: List[str] = []
    matching_skills: List[str] = []
    experience_delta: Optional[str] = None
    reasoning: Optional[str] = None
    verdict: Optional[str] = None

class MatchBatchResultV2(BaseModel):
    parsed_cv: Optional[Dict[str, Any]] = None
    total_jobs_processed: int
    results: List[JobOfferMatchResult]


class CandidateResult(BaseModel):
    cv_id: str
    score: float
    details: str
    rank: int = 0
    matching_skills: List[str] = []
    missing_skills: List[str] = []
    reasoning: Optional[str] = None


class SearchMode(str, Enum):
    VECTOR = "vector"
    HYBRID = "hybrid"


class CandidateSearchRequest(BaseModel):
    top_k: int = Field(default=5, ge=1, le=50)
    mode: SearchMode = SearchMode.VECTOR


class RAGQueryRequest(BaseModel):
    """Request body for RAG-based candidate insights."""
    query: str = Field(..., min_length=5, max_length=2000)
    use_hybrid: bool = False


class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[str]
    context_count: int


class HealthResponse(BaseModel):
    status: str
    version: str
    db_stats: Optional[Dict[str, Any]] = None


# ── Scraping Schemas ───────────────────────────────────────────

class ScrapeJobRequest(BaseModel):
    """Request to scrape a job posting from a URL."""
    url: str = Field(..., min_length=10)


class ScrapeJobResponse(BaseModel):
    """Response from a scrape operation."""
    status: str
    job_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    url: str


class BatchScrapeRequest(BaseModel):
    """Batch scrape multiple job URLs."""
    urls: List[str] = Field(..., min_length=1, max_length=20)


# ── CV + Job Search Schemas ────────────────────────────────────

class JobSearchRequest(BaseModel):
    """Request body for the CV-first job search endpoint."""
    job_title: str = Field(..., min_length=2, max_length=200, description="Job title to search for on LinkedIn")
    location: str = Field(default="", max_length=100, description="Optional location filter (e.g. 'France')")
    max_results: int = Field(default=50, ge=1, le=50, description="Number of job offers to return")


class JobOfferResult(BaseModel):
    """A single ranked job offer from the search results."""
    rank: int
    score: float
    title: str
    company: str
    location: str
    url: str
    platform: str
    salary: str
    job_type: str
    description_preview: str


class CVSummary(BaseModel):
    """Parsed summary of the submitted CV."""
    filename: str
    name: str
    email: str
    skills: List[str]
    summary: str


class JobSearchResponse(BaseModel):
    """Full response from the CV + job title search endpoint."""
    cv_summary: CVSummary
    job_title_searched: str
    location: str
    total_found: int
    results: List[JobOfferResult]

