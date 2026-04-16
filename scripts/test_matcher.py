import sys
import os
import asyncio
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.matcher import Matcher

# Mock dependencies
class MockService:
    async def embed(self, text):
        return []

class MockRAG:
    pass

async def test_matcher():
    print("Initializing Matcher with Cross-Encoder...")
    matcher = Matcher(MockService(), MockRAG())
    
    cv_text = "Experienced software engineer with 5 years in Python, FastAPI, and machine learning."
    
    job_description_1 = "Looking for a Python developer with experience in AI and web frameworks."
    job_description_2 = "Hiring a Chef for a 5-star restaurant. Must know how to cook Italian food."
    
    print("\n--- Test Case 1: Relevant Match ---")
    print(f"CV: {cv_text}")
    print(f"JD: {job_description_1}")
    result_1 = await matcher.match(cv_text, job_description_1)
    print(f"Result: {result_1}")
    
    print("\n--- Test Case 2: Irrelevant Match ---")
    print(f"CV: {cv_text}")
    print(f"JD: {job_description_2}")
    result_2 = await matcher.match(cv_text, job_description_2)
    print(f"Result: {result_2}")
    
    if result_1['score'] > result_2['score']:
        print("\nSUCCESS: Relevant match has higher score.")
    else:
        print("\nFAILURE: Relevant match should have higher score.")

if __name__ == "__main__":
    asyncio.run(test_matcher())
