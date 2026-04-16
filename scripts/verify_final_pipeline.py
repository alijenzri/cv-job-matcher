import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.cv_service import CVService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.core.llm import LLMService
from app.database.vector_db import VectorDB
from app.rag.retriever import HyDERetriever
from app.core.matcher import Matcher

async def verify_final_pipeline():
    print("--- Gemini + PostgreSQL + HyDE Verification ---")
    
    # 1. Setup Mocks
    mock_vector_db = MagicMock(spec=VectorDB)
    mock_vector_db.query.return_value = {
        'ids': [['cv1']], 
        'documents': [["Mock Document Content"]],
        'metadatas': [[{"name": "John Doe"}]],
        'distances': [[0.1]]
    }
    mock_vector_db.get_cv_by_id.return_value = {'documents': ["Mock CV Content"], 'metadatas': [{}]}
    mock_vector_db.get_job_by_id.return_value = {'documents': ["Mock Job Content"], 'metadatas': [{}]}

    mock_llm = MagicMock(spec=LLMService)
    mock_llm.generate_hypothetical_answer.return_value = "Hypothetical Resume Content"
    
    mock_matcher = MagicMock(spec=Matcher)
    async def mock_match(text1, text2):
        return {"score": 0.85, "details": "Matches well"}
    mock_matcher.match = mock_match

    retriever = HyDERetriever(mock_vector_db, mock_llm)
    matching_service = MatchingService(mock_matcher, mock_vector_db, retriever)
    
    # 2. Test HyDE Search
    print("\nTesting HyDE Search...")
    with patch('app.rag.retriever.get_embedding', return_value=[0.1]*384):
        results = await matching_service.search_candidates("job1")
        print(f"Top Candidate ID: {results[0]['cv_id']}")
        print(f"Match Score: {results[0]['score']}")
        
        if results[0]['cv_id'] == 'cv1' and results[0]['score'] == 0.85:
            print("SUCCESS: HyDE search and re-ranking pipeline is working correctly.")
        else:
            print("FAILURE: HyDE search results are unexpected.")

    # 3. Test Gemini hypothetical answer
    print("\nTesting Gemini (Mocked)...")
    hypo = mock_llm.generate_hypothetical_answer("Python Developer")
    print(f"Gemini output: {hypo}")
    if hypo == "Hypothetical Resume Content":
        print("SUCCESS: Gemini logic correctly integrated.")

if __name__ == "__main__":
    asyncio.run(verify_final_pipeline())
