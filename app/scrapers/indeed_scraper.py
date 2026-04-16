"""
Indeed job scraper — production implementation.
"""
from app.scrapers.base_scraper import BaseScraper, ScrapedJob
from app.scrapers.utils import extract_text
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):

    PAGE_TIMEOUT = 25_000  # Indeed can be slow behind Cloudflare

    @property
    def platform(self) -> str:
        return "indeed"

    async def _wait_for_content(self, page):
        """Indeed‑specific: wait for job info header."""
        selectors = [
            "h1.jobsearch-JobInfoHeader-title",
            "h1",
            "[data-testid='jobsearch-JobInfoHeader-title']",
        ]
        for sel in selectors:
            try:
                await page.wait_for_selector(sel, timeout=12_000)
                return
            except Exception:
                continue

    def _parse_page(self, html: str, url: str) -> ScrapedJob:
        soup = BeautifulSoup(html, "html.parser")

        title = extract_text(soup, [
            "h1.jobsearch-JobInfoHeader-title",
            "[data-testid='jobsearch-JobInfoHeader-title']",
            ("h1", {}),
        ], default="Unknown Title")

        company = extract_text(soup, [
            "[data-testid='inlineHeader-companyName']",
            ".jobsearch-InlineCompanyRating-companyHeader a",
            lambda s: s.find("div", {"data-company-name": True}),
        ], default="Unknown Company")

        location = extract_text(soup, [
            "[data-testid='inlineHeader-companyLocation']",
            "[data-testid='job-location']",
            ".jobsearch-JobInfoHeader-subtitle div:last-child",
        ], default="Unknown Location")

        desc_el = soup.find("div", id="jobDescriptionText")
        description = desc_el.get_text(strip=True) if desc_el else ""

        salary = extract_text(soup, [
            "#salaryInfoAndJobType",
            "[data-testid='attribute_snippet_testid']",
            lambda s: s.find("span", class_=lambda c: c and "salary" in c.lower()),
        ], default="Not listed")

        job_type = extract_text(soup, [
            lambda s: s.find("span", string=lambda t: t and any(
                kw in t.lower() for kw in ["full-time", "part-time", "contract", "remote"]
            )),
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
