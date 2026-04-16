"""
API integration tests for CV-Job Matcher.
Tests core endpoints: health, upload, status, job creation, matching, RAG.
"""
import pytest


class TestHealthEndpoint:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "CV-Job Matcher API"

    def test_health(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert data["version"] == "1.0.0"


class TestCVUpload:
    def test_upload_invalid_file_type(self, client):
        """Should reject non-PDF/DOCX files."""
        response = client.post(
            "/api/v1/cv/upload",
            files={"file": ("test.exe", b"fake content", "application/octet-stream")}
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_valid_pdf(self, client):
        """Should accept PDF files and return 202."""
        # Create a minimal valid PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"
        response = client.post(
            "/api/v1/cv/upload",
            files={"file": ("test_cv.pdf", pdf_content, "application/pdf")}
        )
        # Should be 202 Accepted (async processing)
        assert response.status_code == 202
        data = response.json()
        assert "cv_id" in data
        assert data["filename"] == "test_cv.pdf"

    def test_cv_status_not_found(self, client):
        """Should return 404 for non-existent CV."""
        response = client.get("/api/v1/cv/00000000-0000-0000-0000-000000000000/status")
        assert response.status_code == 404


class TestJobEndpoint:
    def test_create_job(self, client):
        """Should create a job description."""
        job_data = {
            "title": "Senior Python Developer",
            "company": "TestCorp",
            "description": "We need an experienced Python developer with FastAPI expertise.",
            "requirements": ["Python", "FastAPI", "PostgreSQL"]
        }
        response = client.post("/api/v1/job", json=job_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Senior Python Developer"
        assert "id" in data


class TestMatchEndpoint:
    def test_match_not_found(self, client):
        """Should return 404 when CV or Job doesn't exist."""
        response = client.post("/api/v1/match", json={
            "cv_id": "00000000-0000-0000-0000-000000000000",
            "job_id": "00000000-0000-0000-0000-000000000001"
        })
        assert response.status_code == 404


class TestRAGEndpoint:
    def test_rag_query_validation(self, client):
        """Should reject queries that are too short."""
        response = client.post("/api/v1/rag/query", json={"query": "hi"})
        assert response.status_code == 422  # Validation error
