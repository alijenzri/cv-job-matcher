"""
Glassdoor job scraper — production implementation.
Glassdoor is the most aggressive at blocking scrapers,
so this uses extra stealth and fallback selectors.
"""
from app.scrapers.base_scraper import BaseScraper, ScrapedJob
from app.scrapers.utils import extract_text
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class GlassdoorScraper(BaseScraper):

    MAX_RETRIES = 2  # Glassdoor blocks aggressively — fewer retries to avoid IP bans
    PAGE_TIMEOUT = 20_000

    @property
    def platform(self) -> str:
        return "glassdoor"

    async def _wait_for_content(self, page):
        """Glassdoor-specific: classes change weekly, try multiple."""
        selectors = [
            "div[class*='JobDetails_jobTitle']",
            "div[class*='jobTitle']",
            "h1",
        ]
        for sel in selectors:
            try:
                await page.wait_for_selector(sel, timeout=10_000)
                return
            except Exception:
                continue

        # Glassdoor often shows a login modal — try to dismiss it
        try:
            close_btn = await page.query_selector("button[class*='CloseButton']")
            if close_btn:
                await close_btn.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass

    def _parse_page(self, html: str, url: str) -> ScrapedJob:
        soup = BeautifulSoup(html, "html.parser")

        title = extract_text(soup, [
            lambda s: s.find("div", class_=lambda c: c and "JobDetails_jobTitle" in c),
            lambda s: s.find("div", class_=lambda c: c and "jobTitle" in c),
            ("h1", {}),
        ], default="Unknown Title")

        company = extract_text(soup, [
            lambda s: s.find("div", class_=lambda c: c and "JobDetails_jobCompany" in c),
            "div.employerName",
            lambda s: s.find("div", class_=lambda c: c and "companyName" in c),
        ], default="Unknown Company")

        location = extract_text(soup, [
            lambda s: s.find("div", class_=lambda c: c and "JobDetails_location" in c),
            lambda s: s.find("div", class_=lambda c: c and "location" in c.lower()),
        ], default="Unknown Location")

        desc_el = (
            soup.find("div", class_=lambda c: c and "JobDetails_jobDescription" in c)
            or soup.find("div", id="JobDescriptionContainer")
            or soup.find("div", class_=lambda c: c and "jobDescription" in c)
        )
        description = desc_el.get_text(strip=True) if desc_el else ""

        rating = extract_text(soup, [
            lambda s: s.find("span", class_=lambda c: c and "rating" in c.lower()),
        ], default=None)

        salary = extract_text(soup, [
            lambda s: s.find("span", class_=lambda c: c and "salary" in c.lower()),
        ], default="Not listed")

        return ScrapedJob(
            title=title,
            company=company,
            location=location,
            description=description,
            salary=salary,
            rating=rating,
            url=url,
            platform=self.platform,
        )
