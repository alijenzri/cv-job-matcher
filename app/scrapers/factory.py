"""
Factory for job scrapers.
"""
from urllib.parse import urlparse
from app.scrapers.linkedin_scraper import LinkedInScraper
from app.scrapers.indeed_scraper import IndeedScraper
from app.scrapers.glassdoor_scraper import GlassdoorScraper

class ScraperFactory:
    @staticmethod
    def get_scraper(url: str):
        """Returns the appropriate scraper instance based on the URL domain."""
        domain = urlparse(url).netloc.lower()
        
        if "linkedin.com" in domain:
            return LinkedInScraper()
        elif "indeed.com" in domain:
            return IndeedScraper()
        elif "glassdoor.com" in domain:
            return GlassdoorScraper()
        else:
            raise ValueError(f"No scraper available for domain: {domain}")
