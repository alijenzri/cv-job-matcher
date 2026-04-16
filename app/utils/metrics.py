"""
Production metrics collection using Prometheus client.
Tracks API latency, task throughput, model inference times, and error rates.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time
import logging
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# ── Counters ───────────────────────────────────────────────────

cv_uploads_total = Counter(
    "cv_uploads_total",
    "Total CV uploads received",
    ["status"]  # success, failed, rejected
)

scrape_requests_total = Counter(
    "scrape_requests_total",
    "Total scrape requests",
    ["platform", "status"]  # linkedin/indeed/glassdoor, success/failed
)

rag_queries_total = Counter(
    "rag_queries_total",
    "Total RAG queries processed",
    ["mode"]  # vector, hybrid
)

match_requests_total = Counter(
    "match_requests_total",
    "Total match requests",
    ["type"]  # single, batch, candidates
)


# ── Histograms (latency) ──────────────────────────────────────

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request latency",
    ["method", "endpoint", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

embedding_duration = Histogram(
    "embedding_duration_seconds",
    "Embedding generation latency",
    ["batch_size"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

cross_encoder_duration = Histogram(
    "cross_encoder_duration_seconds",
    "Cross-Encoder re-ranking latency",
    ["batch_size"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

llm_call_duration = Histogram(
    "llm_call_duration_seconds",
    "LLM API call latency",
    ["operation"],  # generate, hyde, structured_extract
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

scrape_duration = Histogram(
    "scrape_duration_seconds",
    "Web scraping latency",
    ["platform"],
    buckets=[1.0, 5.0, 10.0, 20.0, 30.0]
)


# ── Gauges ─────────────────────────────────────────────────────

active_celery_tasks = Gauge(
    "active_celery_tasks",
    "Number of currently running Celery tasks"
)

db_pool_connections = Gauge(
    "db_pool_connections",
    "Active database pool connections"
)


# ── App info ───────────────────────────────────────────────────

app_info = Info("cv_matcher", "CV-Job Matcher application info")
app_info.info({
    "version": "1.0.0",
    "embedding_model": "all-MiniLM-L6-v2",
    "cross_encoder": "ms-marco-MiniLM-L-6-v2",
})


# ── Timer Helper ───────────────────────────────────────────────

@contextmanager
def track_time(histogram, **labels):
    """Context manager to time a block and record to a Prometheus histogram."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        histogram.labels(**labels).observe(duration)


def timed(histogram, **label_defaults):
    """Decorator version of track_time."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with track_time(histogram, **label_defaults):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with track_time(histogram, **label_defaults):
                return func(*args, **kwargs)

        if hasattr(func, '__wrapped__') or str(func).startswith('<coroutine'):
            return async_wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
