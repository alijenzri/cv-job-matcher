import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.matcher import Matcher
from app.core.llm import LLMService

async def test_matcher_intelligence():
    print("\n=== Testing Matcher Intelligence Layer ===")
    
    cv_text = """
    Jane Doe
    Senior Software Engineer with 8 years of experience in Python, FastAPI, and AWS.
    Built large-scale distributed systems using Kafka and PostgreSQL.
    Expert in React and Node.js for frontend/backend integration.
    """
    
    job_description = """
    Principal Python Engineer
    10+ years of experience required.
    Must have deep expertise in FastAPI, PostgreSQL, and Cloud Architecture.
    Experience with Go or Rust is a plus for performance optimization.
    Must lead a team of 5 engineers.
    """
    
    matcher = Matcher()
    
    print("Running match analysis...")
    result = await matcher.match(cv_text, job_description)
    
    print("\n[MATCH RESULT]")
    print(json.dumps(result, indent=2))
    
    if "verdict" in result and "reasoning" in result:
        print("\n[SUCCESS] Intelligence Layer fields present.")
    else:
        print("\n[ERROR] Missing intelligence fields.")

async def main():
    try:
        await test_matcher_intelligence()
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
