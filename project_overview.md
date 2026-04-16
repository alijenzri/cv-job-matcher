# CareerSeed: System Architecture & Data Flow

This document provides a deep dive into the high-level design of the CareerSeed ecosystem, showcasing how the isolated Microservices communicate and execute tasks.

## 🏗️ Microservices Architecture

CareerSeed is divided into two primary brains, communicating over HTTP:

1. **The .NET Main Server (C#)**
   - Acts as the primary backend, API gateway, and database manager for users, authentication, course progress, and UI interactions.
   - Any heavy AI task is deferred across the network to the Python engine.

2. **The AI Engine Microservice (Python FastAPI)**
   - A highly isolated, mathematically dense environment. Designed specifically because Python dominates the AI ecosystem (PyTorch, SentenceTransformers).
   - Entirely stateless in nature for job scraping and matching—meaning you can horizontally scale this Docker container as traffic increases without any database synchronization errors.

## 🧠 Core Components

- **FastAPI:** The high-performance Python web framework, handling concurrent asynchronous requests, critical for slow AI model generation.
- **Cross-Encoder (`ms-marco-MiniLM`):** Instead of standard vector embeddings (which measure pure semantic similarity), the Cross-Encoder relies on an Attention Mechanism between two documents. It evaluates "Does this candidate's history solve the requirements of this job description?" generating much higher accuracy.
- **Gemini 2.5 Flash:** Used exclusively as an "Intelligence Extraction/Enrichment" layer. Due to token costs, it is strictly forbidden from processing 1000s of jobs. Instead, the Cross-Encoder ranks the jobs first, and Gemini is only invoked for the Top-5 results to generate human-readable feedback.
- **ChromaDB / VectorDB:** Used locally to store CV vectors, enabling high-speed mathematical nearest-neighbor querying.

## 🌊 Complete Data Flow: CV to Recommended Jobs

When a user submits a CV, the system orchestrated the following pipeline:

1. **Ingestion & Parsing:**
   - The PDF is uploaded. `app/core/cv_processor.py` rips raw string text from the PDF using `pikepdf`.
   - Before hitting the database, the raw string is hurled at Gemini to extract structured JSON metadata (Name, Email, Summary).

2. **Job Data Retrieval (Scraping OR Direct Array):**
   - *If using `/cv/search-jobs`:* The proxy fires up live HTTP requests to LinkedIn search pages. It parses HTML nodes, finds job links, and executes heavy concurrent web-requests to download up to 50 raw descriptions.
   - *If using `/matchV2`:* The .NET server simply passes Adzuna's job JSON array directly to the Python server over the network.

3. **Mathematical Ranking (The Cross-Encoder):**
   - The parsed CV text and all 50 Job Descriptions are mapped together into an array of Pairs: `[(CV, Job1), (CV, Job2), ...]`.
   - The PyTorch neural network processes these pairs simultaneously on CPU/GPU.
   - The model generates uncalibrated "Logits" (e.g. `-5.3`, `2.1`).
   - A Linear Threshold Mapping algorithm safely maps these logits mathematically into a `0% - 100%` human-readable score. The jobs are sorted in Descending Order.

4. **Intelligence Enrichment Layer:**
   - Returning just a percentage score isn't enough for a premium user experience.
   - The system slices the array to isolate the **Top 5 Jobs**.
   - It fires off 5 highly concurrent API requests to Gemini. Gemini acts as a Virtual Recruiter, asked to provide a 2-sentence summary of the candidate's fit and critically spot the specific "Missing Skills".

5. **Response Delivery:**
   - The FastApi responds explicitly with a rich JSON document detailing the user's parsed profile, the jobs evaluated, the mathematics, and the deep qualitative feedback from the LLM. The .NET server unwraps this and renders it beautifully on Angular.
