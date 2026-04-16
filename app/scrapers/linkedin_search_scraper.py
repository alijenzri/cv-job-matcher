"""
LinkedIn Job Search Scraper.
Scrapes LinkedIn public job search results by keyword/title.
Uses Playwright stealth to avoid bot detection.
Returns a list of job URLs and basic info from the search result page.
"""
from app.scrapers.base_scraper import BaseScraper, ScrapedJob
from app.scrapers.utils import get_browser_args
from bs4 import BeautifulSoup
import urllib.parse
import asyncio
import logging

logger = logging.getLogger(__name__)


class LinkedInSearchScraper:
    """
    Scrapes LinkedIn's public job search listings for a given job title.
    Returns up to `max_results` job listing URLs for further detail scraping.
    """

    PAGE_TIMEOUT = 25_000

    async def search_jobs(self, job_title: str, location: str = "", max_results: int = 50) -> list[dict]:
        """
        Search LinkedIn jobs by title. Handles Windows event loop issues by running
        in a separate thread if necessary.
        """
        from app.scrapers.utils import run_in_proactor_thread
        
        # We call the internal async method via our proactor thread utility
        return await asyncio.to_thread(
            run_in_proactor_thread, 
            self._search_jobs_internal(job_title, location, max_results)
        )

    async def _search_jobs_internal(self, job_title: str, location: str, max_results: int) -> list[dict]:
        from playwright.async_api import async_playwright

        keywords = urllib.parse.quote(job_title)
        loc = urllib.parse.quote(location) if location else ""
        base_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}"
        if loc:
            base_url += f"&location={loc}"

        logger.info(f"[linkedin-search] Searching LinkedIn jobs: '{job_title}' in '{location or 'Any'}'")

        jobs = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(**get_browser_args())
            page = await context.new_page()

            try:
                await page.goto(base_url, wait_until="domcontentloaded", timeout=self.PAGE_TIMEOUT)
                await page.wait_for_timeout(3000)

                # Scroll to load more jobs (LinkedIn lazy-loads results)
                for _ in range(5):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Parse job cards from search results
                job_cards = soup.select("div.base-card") or soup.select("li.jobs-search__results-list > div")

                if not job_cards:
                    # Try alternate selectors
                    job_cards = soup.select("ul.jobs-search__results-list li")

                logger.info(f"[linkedin-search] Found {len(job_cards)} job cards in page")

                for card in job_cards[:max_results]:
                    try:
                        # Title
                        title_el = (
                            card.select_one("h3.base-search-card__title")
                            or card.select_one("h3")
                            or card.select_one("a")
                        )
                        title = title_el.get_text(strip=True) if title_el else "Unknown Title"

                        # Company
                        company_el = (
                            card.select_one("h4.base-search-card__subtitle")
                            or card.select_one("a.hidden-nested-link")
                            or card.select_one("h4")
                        )
                        company = company_el.get_text(strip=True) if company_el else "Unknown Company"

                        # Location
                        loc_el = (
                            card.select_one("span.job-search-card__location")
                            or card.select_one("span.base-search-card__metadata")
                        )
                        job_location = loc_el.get_text(strip=True) if loc_el else location or "Unknown"

                        # URL
                        link_el = card.select_one("a.base-card__full-link") or card.select_one("a[href*='/jobs/view/']")
                        job_url = ""
                        if link_el:
                            job_url = link_el.get("href", "")
                            # Clean tracking params
                            if "?" in job_url:
                                job_url = job_url.split("?")[0]

                        if not job_url:
                            continue

                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": job_location,
                            "url": job_url,
                            "platform": "linkedin",
                        })
                    except Exception as e:
                        logger.debug(f"Failed to parse job card: {e}")
                        continue

            except Exception as e:
                logger.error(f"[linkedin-search] Search failed: {e}")
            finally:
                await browser.close()

        logger.info(f"[linkedin-search] Collected {len(jobs)} job listings")
        return jobs
