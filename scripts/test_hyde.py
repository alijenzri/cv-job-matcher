import sys
import os
import asyncio

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.rag_system import RAGSystem
from app.config import settings

async def test_hyde():
    print("Initializing RAG System...")
    try:
        rag = RAGSystem()
    except Exception as e:
        print(f"Failed to initialize RAG System: {e}")
        return

    query = "What are the key trends in the IT industry?"
    print(f"\nQuerying: {query}")
    
    try:
        response = await rag.query(query)
        print("\nResponse:")
        print(response)
    except Exception as e:
        print(f"Error during query: {e}")

if __name__ == "__main__":
    if not settings.OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY not found in environment. HyDE will fail.")
    asyncio.run(test_hyde())
