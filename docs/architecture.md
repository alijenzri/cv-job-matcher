# CareerSeed AI - Deep Architecture Guide

This document explores the dense technical architecture of the AI service, providing exhaustive explanations for every library, model, and workflow decision inside the `cv-job-matcher` directory.

## 🧱 The Core Foundation

The project moves away from typical REST APIs and uses a pipeline architecture to orchestrate synchronous math operations alongside asynchronous I/O (File reading, web scraping, and LLM calls).

### Technical Stack & Decisions:
- **FastAPI:** Chosen because standard frameworks like Flask block the execution thread while waiting for Google's Gemini to respond. FastAPI uses `async/await` inherently, allowing node-like concurrency.
- **Uvicorn:** The ASGI server holding the FastAPI threads.
- **Pydantic (Schemas):** Forces strict Data Type Validation. If the .NET application sends a String instead of an Integer for `max_results`, Pydantic automatically rejects it with an HTTP 422, preserving Python's data integrity.

## 🧠 The AI Brain Split

Instead of utilizing one massive LLM like GPT-4 to do everything, CareerSeed splits the AI into two highly specialized domains: **Quantitative Ranking** (Cross-Encoder) and **Qualitative Intelligence** (Gemini).

### 1. Quantitative Engine (PyTorch Cross-Encoder)
**Model Used:** `ms-marco-MiniLM-L-6-v2`
- **What it is:** A Deep Learning transformer model hosted via SentenceTransformers.
- **Why we use it:** If you ask an LLM to rank 50 separate jobs against a CV, it takes 3+ minutes and costs excessive tokens. The Cross-Encoder is an Attention-Mechanism model running directly on your CPU. It "reads" both the CV and Job Description simultaneously, looking for overlapping semantic contexts, returning a raw mathematical score (Logit) in fractions of a second.
- **The Catch:** MS-MARCO models were trained for Bing search engines. Their raw output bounds drift wildly between `-15` and `+10`. We pass these raw logits through a custom algorithms inside `matcher.py:normalize_logit` to squash the output mathematically back into a human-readable `0%` to `100%` scale.

### 2. Qualitative Intelligence (Gemini 2.5 Flash)
**Model Used:** `models/gemini-2.5-flash`
- **What it is:** Google's latest multimodal generative AI.
- **Why we use it:** Once the Cross-Encoder ranks the Top 5 jobs, we need to tell the user *why* they matched. The Cross-Encoder cannot generate text, only numbers. Gemini takes the candidate's CV and the job's requirements and writes a professional two-sentence summary outlining what the candidate lacks (Missing Skills) to push their match from 80% to 100%.
- **Robustness:** We force Gemini to output its response as pure JSON via System Prompts.

## 🌐 The Search / Data Modules

The system must acquire jobs before it can rank them. 
It supports two distinct pathways:

### Pathway A: `MatchV2` (Injected Data)
Ideal for pre-existing databases. The C# Backend already called Adzuna, received an array of 50 jobs, and passed them directly to Python. 
1. `matcher.py` tokenizes the array.
2. It assigns scores.
3. Top 5 are enriched.

### Pathway B: `/cv/search-jobs` (Autonomous Scraping)
Ideal for dynamic searching when APIs are restricted.
1. The user uploads a CV and requests "React Dev" in "London".
2. `linkedin_search_scraper.py` (an autonomous scraper using `httpx` and BeautifulSoup4) forms a live URL: `https://www.linkedin.com/jobs/search?keywords=React+Dev&location=London`.
3. It downloads the raw HTML and traverses the DOM Tree to scrape all H3 job titles, Anchor tag URLs, and company `div` names.
4. It then recursively loops through all 50 scraped URL links, downloads the individual job pages, and rips out the specific raw text inside `<div class="description">`.
5. Finally, it sends these 50 raw descriptions back into Pathway A for ranking.
