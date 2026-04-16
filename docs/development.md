# CareerSeed AI - Development Guide

This guide is for Machine Learning engineers or Backend developers who wish to modify, extend, or debug the Python/FastAPI codebase.

## 🏗️ Folder Structure Overview

```
cv-job-matcher/
├── app/
│   ├── api/             # FastAPI configuration. Contains `routes.py`, `schemas.py`, and `dependencies.py`.
│   ├── core/            # The Brains: `llm.py` (Gemini API), `matcher.py` (PyTorch CrossEncoder logic).
│   ├── database/        # Storage bindings. Currently initializes local file-based ChromaDB.
│   ├── ml/              # Lightweight embeddings models and fallback NLP tools.
│   ├── scrapers/        # Web Scraping tools (LinkedIn, BaseScrapers) via bs4 and HTTPX.
│   └── services/        # Business Logic / Use-Cases orchestrating interactions.
├── scratch/             # Temporary files generated during CV processing
├── .env                 # Secret Keys and Config configurations.
├── requirements.txt     # Python dependency locks.
└── main.py              # Uvicorn ASGI Application entry point.
```

## 🛠️ Modifying Core Behaviors

### 1. Replacing Google Gemini with OpenAI or Claude
The system is deeply abstracted. If Google Gemini is hitting rate limits or you wish to upgrade to GPT-4o:
1. Open `app/core/llm.py`.
2. Delete the `google.genai` SDK references.
3. Import the `openai` SDK.
4. Modify the `generate_structured_json` method to utilize OpenAI arguments (`response_format={ "type": "json_object" }`).
5. **No other files need to change.** The `MatchingService` effortlessly receives standard JSON dictionary outputs regardless of the underlying LLM!

### 2. Upgrading the Mathematics (The Cross Encoder)
Currently, `app/core/matcher.py` loads `cross-encoder/ms-marco-MiniLM-L-6-v2`. This model is globally renowned for fast inference on CPUs, but it is notoriously generic.
1. To implement an HR-specific model, find a model specialized in candidate-to-job NLP on HuggingFace.
2. In `app/config.py`, change `CROSS_ENCODER_MODEL = "new-model-name"`.
3. If the new model predicts differently, you must tweak the `normalize_logit()` function within `matcher.py` to map the new model's output bounds gracefully to a `0-100` range.

### 3. Adding New Web Scrapers
To add Indeed or Glassdoor:
1. Copy `linkedin_search_scraper.py` into a new file `indeed_scraper.py`.
2. Extend `app.scrapers.base_scraper.BaseScraper`.
3. Overwrite the `scrape()` method, targeting Indeed-specific HTML `<div>` classes or IDs using BeautifulSoup.
4. Update `app/services/job_search_service.py` to leverage the new module when a user requests an Indeed search.

## 🐛 Debugging Best Practices

- **CV Failed To Parse?** PDF extraction is fragile. If a user submits an image-based PDF, `pikepdf` will fail. Look in `app/core/cv_processor.py`. A future enhancement would be connecting `pytesseract` or AWS Textract to read image-based text.
- **LLM Error 503:** The log output will dictate if the API is failing. Because generation happens asynchronously, monitor the console logs—our code naturally falls back and suppresses fatal crashes to keep the main thread alive, meaning your UI might just show "Intelligence Data Missing".
- **422 Unprocessable Entity:** This means your .NET application failed to match the strict Data-Type expectations set in `app/api/schemas.py`. Check your casing, and ensure `UploadFile` headers use true `multipart/form-data` wrappers via the C# `HttpClient` boundaries.
