# CareerSeed AI - CV-Job Matcher & Search Engine

Welcome to the **CareerSeed AI Matcher**, the core Python microservice responsible for analyzing candidate CVs, executing massive live job searches, and applying deep artificial intelligence to rank candidate-to-job fit.

## 🚀 Project Overview

The traditional recruitment process is broken, relying on strict keyword matching that filters out passionate candidates lacking specific buzzwords. CareerSeed solves this by reading CVs the way a senior technical recruiter does: understanding context, semantic meaning, and transferable skills.

**Key Features:**
- **Intelligent CV Parsing:** Extracts text from PDFs/DOCX and uses Gemini to structure it into readable intelligence (Name, Email, Skills).
- **Batch Job Matching (MatchV2):** Accepts enormous batches of job descriptions (from Adzuna or elsewhere) and mathematically scores them against a CV instantly.
- **Deep LLM Enrichment:** Auto-generates the "why" behind a match. Extensively detailing missing skills, matching skills, and a verdict.
- **Live LinkedIn Search:** Performs real-time scraping of platforms like LinkedIn to discover and rank the top 50 freshest jobs on the market tailored perfectly to your uploaded CV.

## ⚙️ Requirements & Installation

This project is built for speed and mathematical precision. 

### Prerequisites
- Python 3.10+
- PostgreSQL (Locally installed and running)
- *Optional:* Docker (if you wish to enable Celery/Redis for background jobs, though the app safely falls back without it)

### Setup Steps
1. **Clone & Virtual Environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**
   Open the `.env` file and ensure your API keys and Database connections are set:
   - `GOOGLE_API_KEY`: Your Gemini API key.
   - `DATABASE_URL`: Connection string to PostgreSQL.
4. **Run the Server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   The API will be live at `http://127.0.0.1:8000`. You can view the Auto-Generated Swagger documentation at `http://127.0.0.1:8000/docs`.

## 📂 Project Structure & Development Guide

The project strictly follows Domain-Driven Design (DDD) to keep concerns separated:

- `app/api/` → Contains **FastAPI routes and Schemas**. If you want to modify endpoints or JSON request/response structures, start here (`routes.py`, `schemas.py`).
- `app/core/` → Contains the **AI engine**. `matcher.py` houses the Cross-Encoder mathematics, and `cv_processor.py` houses the Gemini interaction.
- `app/services/` → The **Business Logic**. Routes should be "dumb" and pass all data to these services (`matching_service.py`, `job_search_service.py`).
- `app/scrapers/` → The **Live Data engines**. Web scrapers utilizing HTTPX and BeautifulSoup to read LinkedIn html.
- `app/database/` → Abstractions for connecting to PostgreSQL and local ChromaDB Vector storage.

### Extending the System
- **Adding a new Job Board Scraper:** Create a new file in `app/scrapers/` extending `BaseScraper`. Add the CSS selectors required to pull descriptions, and hook it into `job_search_service.py`.
- **Replacing the AI Model:** If you wish to switch from `Gemini` to `OpenAI`, simply update the API calls within `app/core/llm.py`—the rest of the application will continue to function seamlessly.

## 🧑‍💻 User Guide
1. Launch the server.
2. Head to `localhost:8000/docs`.
3. Try the `/api/v1/cv/search-jobs` endpoint:
   - Enter your desired `job_title` (e.g. "Software Engineer").
   - Enter your `location` (e.g. "Remote" or "London").
   - Click "Choose File" and upload your CV (`.pdf`).
   - Execute! Within 60 seconds, the engine will scrape the web, read 50+ descriptions, and hand you back a perfectly ranked json array of the roles you have the highest mathematical chance of landing.
