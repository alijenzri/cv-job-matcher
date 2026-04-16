"""
Scraper utilities: stealth browser config, HTML cleaning, rate limiter.
"""
import re
import asyncio
import time
from bs4 import BeautifulSoup
import logging

import sys
import threading
import concurrent.futures

logger = logging.getLogger(__name__)


def run_in_proactor_thread(coro):
    """
    Runs an asymmetric coroutine in a dedicated thread with its own ProactorEventLoop.
    Essential for Windows users running Uvicorn with --reload, as that forces
    SelectorEventLoop which lacks subprocess support required by Playwright.
    """
    if sys.platform != "win32":
        return asyncio.run(coro)

    def _run():
        # Force a new Proactor loop in this thread
        loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        return future.result()


def clean_html(html_content: str) -> str:
    """Remove tags, scripts, and styles from raw HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(["script", "style", "nav", "footer", "header", "iframe"]):
        tag.extract()
    text = soup.get_text(separator=' ', strip=True)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text


def get_browser_args() -> dict:
    """
    Returns stealth browser context options for Playwright.
    Mimics a real Chrome session to reduce bot detection.
    """
    return {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "color_scheme": "light",
        "extra_http_headers": {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    }


def extract_text(soup: BeautifulSoup, selectors: list, default: str = "") -> str:
    """
    Try multiple CSS selectors or tag searches in order, return first match.
    Each selector can be:
      - A tuple: ('tag', {'attr': 'value'})
      - A callable lambda on soup
    """
    for selector in selectors:
        try:
            if callable(selector):
                el = selector(soup)
            elif isinstance(selector, tuple):
                el = soup.find(*selector)
            else:
                el = soup.select_one(selector)

            if el:
                return el.get_text(strip=True)
        except Exception:
            continue
    return default


class RateLimiter:
    """
    Token-bucket rate limiter for polite scraping.
    Ensures we don't exceed N requests per minute per scraper.
    """

    def __init__(self, requests_per_minute: int = 10):
        self.interval = 60.0 / requests_per_minute
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self.interval:
                wait = self.interval - elapsed
                logger.debug(f"Rate limiter: waiting {wait:.2f}s")
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()
