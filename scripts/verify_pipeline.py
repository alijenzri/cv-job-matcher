import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.cv_service import CVService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.database.vector_db import VectorDB
from app.core.cv_processor import CVProcessor
from app.rag.retriever import HyDERetriever
from app.core.matcher import Matcher

class MockLLMService:
    def generate_text(self, prompt, system_prompt):
        return '{"name": "John Doe", "skills": ["Python", "AI"], "summary": "Senior Dev"}'
    
    def generate_hypothetical_answer(self, query):
        return "Ideal candidate has Python, SQL, and 5 years experience."

class MockFile:
    def __init__(self, filename, content):
        self.filename = filename
        self.file = MagicMock()
        # file.read is not used, we blindly copyfileobj in implementation. 
        # But we mocked process() so we don't hit file system.

async def run_verification():
    print("Initializing components...")
    
    # Mock VectorDB to avoid filesystem IO/Chroma issues if not set up
    # We want to verify wiring, not Chroma itself right now
    mock_vector_db = MagicMock(spec=VectorDB)
    # Explicitly set the collection attributes since they are instance vars
    mock_vector_db.cv_collection = MagicMock()
    mock_vector_db.job_collection = MagicMock()
    
    mock_vector_db.get_cv_by_id.return_value = {"ids": ["cv1"], "documents": ["CV Content: Python Developer"]}
    mock_vector_db.get_job_by_id.return_value = {"ids": ["job1"], "documents": ["Job Content: Python Expert needed"]}
    # Mocking retrieve return: 
    # { 'ids': [['id1']], 'documents': [['doc1']], ... }
    mock_vector_db.cv_collection.query.return_value = {'ids': [['cv1']], 'documents': [['CV Content: Python Developer']]} 

    # Mock Matcher
    mock_matcher = MagicMock(spec=Matcher)
    mock_matcher.match.return_value = {"score": 0.95, "details": "High match"}
    
    # Init Services with Mocks
    cv_processor = CVProcessor()
    # Mock the extraction to avoid real LLM call
    cv_processor.extract_structured_data = MagicMock(return_value={"name": "Test User", "skills": ["Python"]})
    cv_processor.process = MagicMock(return_value={"text": "CV Content: Python Developer"})
    
    cv_service = CVService(cv_processor, mock_vector_db)
    job_service = JobService(mock_vector_db)
    
    llm_service = MockLLMService()
    # Mock HyDERetriever queries
    # We can use real HyDERetriever class but mock its dependencies (LLM, VectorDB)
    hyde_retriever = HyDERetriever(mock_vector_db, llm_service)
    
    # We need to mock retrieve method of hyde directly if we don't want to rely on VectorDB logic
    # But let's try to let it run logically if possible. 
    # HyDE calls: 1. LLM gen (Mocked) -> 2. Embed (Real?) -> 3. VectorDB Query (Mocked)
    # Embeddings need real SentenceTransformer? It downloads models. Might be slow first time.
    # Let's mock embedding function to return random list.
    with unittest.mock.patch('app.rag.retriever.get_embedding', return_value=[0.1]*384):
        matching_service = MatchingService(mock_matcher, mock_vector_db, hyde_retriever)
        
        print("\n--- Testing Ingestion ---")
        mock_file = MockFile("test_cv.pdf", b"dummy content")
        # Need to patch shutil or open since cv_service tries to write file
        import builtins
        with unittest.mock.patch('builtins.open', unittest.mock.mock_open()), \
             unittest.mock.patch('shutil.copyfileobj'):
            cv_result = await cv_service.upload_cv(mock_file)
            print(f"CV Upload Result: {cv_result}")
            
        print("\n--- Testing Job Creation ---")
        with unittest.mock.patch('app.services.job_service.get_embedding', return_value=[0.1]*384):
             job_result = await job_service.create_job({"title": "Python Dev", "description": "Need Python"})
             print(f"Job Creation Result: {job_result}")
        
        print("\n--- Testing Matching (1:1) ---")
        match_result = await matching_service.create_match("cv1", "job1")
        print(f"Match Result: {match_result}")
        
        print("\n--- Testing Search (HyDE) ---")
        # We need to ensure HyDE calls vector_db.query, and we mocked vector_db.cv_collection.query
        # The retriever calls vector_db.query, which calls self.cv_collection.query
        # We mocked vector_db but we didn't mock the method 'query' itself, we mocked 'cv_collection'.
        # VectorDB.query implementation: return self.cv_collection.query(...)
        # So we need mock_vector_db.query side_effect or return value?
        # In step 63, vector_db.query calls self.cv_collection.query. 
        # Since mock_vector_db is a Mock, calling query() returns a new Mock unless specified.
        # Let's force it.
        mock_vector_db.query.return_value = {'ids': [['cv1']], 'documents': [['CV Content: Python Dev']]}
        
        search_result = await matching_service.search_candidates("job1")
        print(f"Search Result: {search_result}")

if __name__ == "__main__":
    import unittest.mock
    asyncio.run(run_verification())
