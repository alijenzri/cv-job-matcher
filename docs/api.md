# CareerSeed AI - API Documentation

This document covers the details of the highly optimized, stateless ranking endpoints that power the Python Artificial Intelligence Microservice.

---

## 1. Batch Match & Ranking Endpoint (`/api/v1/matchV2`)

This endpoint mathematically ranks a single candidate's CV against an array of externally provided JSON Job Descriptions (such as those retrieved from Adzuna APIs on the .NET Backend side).

### 📍 Endpoint Details
- **URL:** `/api/v1/matchV2`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`

### 📥 Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | `UploadFile` (Binary) | **Yes** | The user's uploaded CV file. Must be standard MIME types (e.g. `application/pdf`, `.txt`, `.docx`). |
| `jobs_data` | `String` (JSON Array) | **Yes** | An unparsed JSON String containing an array of Job Document objects. The backend will manually run `json.loads()` on this string to parse the objects out. |

**Example of `jobs_data` String format:**
```json
[
  {
    "title": "Backend (.NET Core)",
    "company": "TechFusion",
    "description": "Full details of the job listing..."
  },
  {
    "title": "Angular Specialist",
    "company": "WebCorp API",
    "description": "Full details of the next job..."
  }
]
```

### 📤 Response Format (`MatchBatchResultV2`)

**Success Payload (HTTP 200 OK):**
```json
{
  "parsed_cv": {
    "name": "Jane Candidate",
    "email": "jane@example.com",
    "skills": ["C#", "Azure", "Python", "Docker"],
    "summary": "Experienced backend developer with strong cloud exposure..."
  },
  "total_jobs_processed": 2,
  "results": [
    {
      "score": 83.45,
      "title": "Backend (.NET Core)",
      "company": "TechFusion",
      "description_preview": "Full details of the job...",
      "summary": "This candidate is a superb fit due to their C# background.",
      "missing_skills": ["SQL Server Performance Tuning"],
      "matching_skills": ["C#", "Azure", "Docker"],
      "experience_delta": "Provides 4 years vs required 3 years.",
      "verdict": "Strong Match"
    },
    ...
  ]
}
```
*Note:* The array is automatically sorted by `score` in Descending order (best match first). Only the Top 5 results will contain populated `summary` and `missing_skills` fields to optimize Generation AI token costs.

### ❌ Possible Errors
- `422 Unprocessable Entity`: If `jobs_data` is not sent as a string field.
- `400 Bad Request`: If `jobs_data` is a string but fails to parse as a valid JSON Array.
- `503 Service Unavailable`: Bubble-up via internal logging if the Google Gemini API fails.

---

## 2. Live LinkedIn Search & Match Endpoint (`/api/v1/cv/search-jobs`)

This endpoint runs a high-latency, fully autonomous pipeline. It takes a CV and a Search Query, autonomously scrapes live Job Boards (like LinkedIn), reads the pages, and returns ranked results.

### 📍 Endpoint Details
- **URL:** `/api/v1/cv/search-jobs`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`

### 📥 Request Parameters (Headers + File)
*Note: Due to Pydantic compatibility constraints alongside file uploads, custom query parameters are enforced via HTTP Headers.*

| Headers | Type | Required | Description |
|-----------|------|----------|-------------|
| `job-title` | `String` | **Yes** | e.g. "Software Engineer" |
| `location` | `String` | No | Defaults to empty string. e.g "London" |
| `max-results`| `Integer`| No | Target number of jobs to fetch. Max 50. Defaults to 10. |

| Form Data | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | `UploadFile` | **Yes** | Candidate's Resume/CV PDF. |

### 📤 Response Format (`JobSearchResponse`)

```json
{
  "cv_summary": {
    "filename": "jane_cv.pdf",
    "name": "Jane Candidate",
    "email": "jane@example.com",
    "skills": ["C#", "Azure"],
    "summary": "..."
  },
  "job_title_searched": "Software Engineer",
  "location": "London",
  "total_found": 15,
  "results": [
    {
      "rank": 1,
      "score": 90.1,
      "title": "Software Engineer",
      "company": "Finance Tech UK",
      "location": "London",
      "url": "https://linkedin.com/jobs/view/...",
      "platform": "LinkedIn",
      "salary": "Unavailable",
      "job_type": "Full-Time",
      "description_preview": "..."
    }
  ]
}
```
