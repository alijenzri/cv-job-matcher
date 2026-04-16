FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for psycopg2, unstructured PDF parsing)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy model for NER (used by Presidio)
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p data/uploads

# Expose port
EXPOSE 8000

# Run the application with Gunicorn + Uvicorn workers for production
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-"]
