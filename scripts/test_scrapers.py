import asyncio
import sys
import logging
from app.scrapers.linkedin_scraper import LinkedInScraper
from app.scrapers.indeed_scraper import IndeedScraper
from app.scrapers.glassdoor_scraper import GlassdoorScraper

# Setup logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Select Scraper:")
    print("1. LinkedIn")
    print("2. Indeed")
    print("3. Glassdoor")
    
    choice = input("Enter choice (1-3): ").strip()
    url = input("Enter job URL: ").strip()
    
    scraper = None
    if choice == '1':
        scraper = LinkedInScraper()
    elif choice == '2':
        scraper = IndeedScraper()
    elif choice == '3':
        scraper = GlassdoorScraper()
    else:
        print("Invalid choice")
        return

    print(f"Scraping {url}...")
    try:
        result = await scraper.scrape(url)
        print("\n--- RESULTS ---")
        for key, value in result.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
