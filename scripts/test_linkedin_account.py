import asyncio
import os
import sys
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

from app.config import settings
from app.scrapers.utils import get_browser_args

async def test_linkedin_login():
    load_dotenv(override=True)
    
    username = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not username or not password:
        print("Error: LINKEDIN_USERNAME or LINKEDIN_PASSWORD not found in .env")
        return

    print(f"Testing LinkedIn account: {username}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Start headless for now
        context = await browser.new_context(**get_browser_args())
        page = await context.new_page()
        
        try:
            print("Navigating to LinkedIn login page...")
            await page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            
            print("Filling credentials...")
            await page.fill("#username", username)
            await page.fill("#password", password)
            await page.click('button[type="submit"]')
            
            # Wait for navigation or error
            try:
                await page.wait_for_selector(".global-nav", timeout=15000)
                print("Login Successful! Global nav detected.")
                
                # Take a screenshot to verify (headless)
                await page.screenshot(path="linkedin_login_success.png")
                print("Screenshot saved as 'linkedin_login_success.png'")
                
            except Exception:
                print("Login failed or encountered a challenge (CAPTCHA/Verification).")
                # Check for error messages
                error_msg = await page.query_selector(".error-for-password")
                if error_msg:
                    print(f"LinkedIn says: {await error_msg.inner_text()}")
                
                await page.screenshot(path="linkedin_login_failed.png")
                print("Failure screenshot saved as 'linkedin_login_failed.png'")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_linkedin_login())
