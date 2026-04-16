"""
Base scraper with production-grade retry logic, stealth context,
rate-limiting, and structured output normalization.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from app.scrapers.utils import get_browser_args, clean_html, RateLimiter
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ScrapedJob:
    """Normalized output from any scraper. Every scraper returns this shape."""
    title: str = "Unknown Title"
    company: str = "Unknown Company"
    location: str = "Unknown Location"
    description: str = ""
    salary: str = "Not listed"
    job_type: str = "Not listed"
    date_posted: str = "Not listed"
    rating: Optional[str] = None
    url: str = ""
    platform: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_html_length: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def is_valid(self) -> bool:
        """A scrape is valid if we got at least a title and some description."""
        return (
            self.title != "Unknown Title"
            and len(self.description) > 50
            and self.error is None
        )


class BaseScraper(ABC):
    """
    Abstract scraper with built‑in retry, rate‑limiting, and timeout handling.
    Subclasses only need to implement `_parse_page`.
    """

    MAX_RETRIES = 3
    RETRY_BACKOFF = 2  # seconds, multiplied by attempt number
    PAGE_TIMEOUT = 20_000  # ms

    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=10)

    async def scrape(self, url: str) -> Dict[str, Any]:
        """
        Public entrypoint with retry + rate‑limit wrapper.
        Uses run_in_proactor_thread on Windows to avoid loop conflicts.
        """
        await self.rate_limiter.acquire()

        from app.scrapers.utils import run_in_proactor_thread

        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"[{self.platform}] Attempt {attempt}/{self.MAX_RETRIES}: {url}")
                
                # Execute the browser logic in the dedicated proactor thread
                result = await asyncio.to_thread(
                    run_in_proactor_thread,
                    self._scrape_with_browser_internal(url)
                )

                if result.is_valid:
                    logger.info(f"[{self.platform}] ✅ Scraped: {result.title} @ {result.company}")
                    return result.to_dict()
                else:
                    logger.warning(f"[{self.platform}] Incomplete scrape on attempt {attempt}")
                    last_error = "Incomplete data"
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[{self.platform}] Attempt {attempt} failed: {e}")
                if attempt < self.MAX_RETRIES:
                    wait = self.RETRY_BACKOFF * attempt
                    logger.info(f"[{self.platform}] Retrying in {wait}s...")
                    await asyncio.sleep(wait)

        # All retries exhausted
        logger.error(f"[{self.platform}] ❌ All {self.MAX_RETRIES} attempts failed for {url}")
        return ScrapedJob(url=url, platform=self.platform, error=last_error).to_dict()

    async def _scrape_with_browser_internal(self, url: str) -> ScrapedJob:
        """Launch browser, navigate, parse. Internal method for proactor thread."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(**get_browser_args())
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.PAGE_TIMEOUT)

                # Wait for main content signal
                await self._wait_for_content(page)

                # Scroll to trigger lazy‑loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)

                html = await page.content()
                result = self._parse_page(html, url)
                result.raw_html_length = len(html)
                return result

            finally:
                await browser.close()

    async def _wait_for_content(self, page):
        """Override in subclass to wait for platform-specific selectors."""
        try:
            await page.wait_for_selector("h1", timeout=10_000)
        except Exception:
            pass

    @abstractmethod
    def _parse_page(self, html: str, url: str) -> ScrapedJob:
        """
        Parse raw HTML and return a ScrapedJob.
        Subclasses implement this for each platform.
        """
        ...

    @property
    @abstractmethod
    def platform(self) -> str:
        """Return platform name like 'linkedin', 'indeed', etc."""
        ...
