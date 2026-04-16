"""
LinkedIn job scraper — production implementation.
Uses resilient multi-selector parsing for LinkedIn's frequently-changing DOM.
"""
from app.scrapers.base_scraper import BaseScraper, ScrapedJob
from app.scrapers.utils import extract_text
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):

    @property
    def platform(self) -> str:
        return "linkedin"

    async def _wait_for_content(self, page):
        """LinkedIn-specific: wait for job title to render."""
        selectors = [
            "h1",
            ".topcard__title",
            ".job-details-jobs-unified-top-card__job-title",
        ]
        for sel in selectors:
            try:
                await page.wait_for_selector(sel, timeout=8_000)
                return
            except Exception:
                continue

    def _parse_page(self, html: str, url: str) -> ScrapedJob:
        soup = BeautifulSoup(html, "html.parser")

        title = extract_text(soup, [
            "h1.topcard__title",
            ".job-details-jobs-unified-top-card__job-title",
            ("h1", {}),
        ], default="Unknown Title")

        company = extract_text(soup, [
            "a.topcard__org-name-link",
            ".job-details-jobs-unified-top-card__company-name a",
            ".job-details-jobs-unified-top-card__company-name",
            lambda s: s.find("a", class_=lambda c: c and "org-name" in c),
        ], default="Unknown Company")

        location = extract_text(soup, [
            "span.topcard__flavor--bullet",
            ".job-details-jobs-unified-top-card__bullet",
            lambda s: s.find("span", class_=lambda c: c and "location" in c.lower()),
        ], default="Unknown Location")

        # Description — multiple fallback containers
        desc_el = (
            soup.find("div", class_="description__text")
            or soup.find("div", id="job-details")
            or soup.find("div", class_=lambda c: c and "show-more" in c)
        )
        description = desc_el.get_text(strip=True) if desc_el else ""

        # Salary (LinkedIn often hides this behind auth)
        salary = extract_text(soup, [
            ".compensation__salary",
            lambda s: s.find("span", class_=lambda c: c and "salary" in c.lower()),
        ], default="Not listed")

        # Job type (Full-time, Remote, etc.)
        job_type = extract_text(soup, [
            ".description__job-criteria-text",
            lambda s: s.find("span", class_=lambda c: c and "workplace-type" in c.lower()),
        ], default="Not listed")

        return ScrapedJob(
            title=title,
            company=company,
            location=location,
            description=description,
            salary=salary,
            job_type=job_type,
            url=url,
            platform=self.platform,
        )
