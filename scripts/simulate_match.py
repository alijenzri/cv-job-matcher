import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.matcher import Matcher

async def run_simulation():
    print("\n" + "="*60)
    print("CV-JOB MATCHER: INTELLIGENCE LAYER SIMULATION")
    print("="*60)
    
    # ── Input Data ──────────────────────────────────────────────────
    
    cv_text = """
    ALEX RIVERA
    Senior Full Stack Engineer | 10+ Years Experience
    
    SUMMARY:
    Expert in Python (FastAPI, Django) and React/Next.js. 
    Proven track record of building scalable cloud architectures on AWS.
    Lead developer for a microservices platform handling 50k requests/min.
    
    EXPERIENCE:
    - Tech Lead @ Horizon Data Systems (2018 - Present)
      - Migrated legacy monolith to FastAPI/PostgreSQL architecture.
      - Implemented Redis caching reducing latency by 40%.
      - Mentored a team of 6 engineers.
    - Software Engineer @ CloudStream (2014 - 2018)
      - Built real-time analytics dashboards using Node.js and D3.js.
    
    SKILLS:
    Python, FastAPI, AWS (EC2, S3, Lambda), PostgreSQL, Redis, Docker, Kubernetes, React, TypeScript.
    """
    
    job_description = """
    Lead Python Developer (FastAPI)
    
    We are looking for a Lead Python Developer to join our growing engineering team.
    
    REQUIREMENTS:
    - 8+ years of professional software development experience.
    - Deep expertise in Python and modern frameworks like FastAPI or Starlette.
    - Strong experience with PostgreSQL and vector databases (pgvector/Pinecone).
    - Experience in high-performance computing or real-time systems.
    - Previous experience as a Tech Lead or Senior Engineer is mandatory.
    - Experience with Cloud-native development (AWS/GCP).
    
    NICE TO HAVE:
    - Knowledge of RAG (Retrieval-Augmented Generation) and LangChain.
    - Experience with Redis and background task processing (Celery).
    """
    
    # ── Execution ───────────────────────────────────────────────────
    
    print("\n[STEP 1] Initializing Matching Engine...")
    matcher = Matcher()
    
    print("[STEP 2] Performing Deep Intelligence Match Analysis...")
    result = await matcher.match(cv_text, job_description)
    
    # ── Output Report ───────────────────────────────────────────────
    
    print("\n" + "-"*60)
    print("MATCH INTELLIGENCE REPORT")
    print("-"*60)
    
    print(f"VERDICT:           {result.get('verdict', 'N/A').upper()}")
    print(f"RELEVANCE SCORE:   {result.get('score', 0)} / 10")
    print("\n[AI REASONING]")
    print(result.get('reasoning', 'No reasoning provided.'))
    
    print("\n[TOP MATCHING SKILLS]")
    for skill in result.get('matching_skills', []):
        print(f" [MATCH] {skill}")
        
    print("\n[CRITICAL GAPS / MISSING SKILLS]")
    gaps = result.get('missing_skills', [])
    if gaps:
        for gap in gaps:
            print(f" [GAP] {gap}")
    else:
        print(" No critical gaps detected.")
        
    print("\n[EXPERIENCE DELTA]")
    print(result.get('experience_delta', 'N/A'))
    
    print("\n" + "="*60)
    print("SIMULATION COMPLETE")
    print("="*60 + "\n")



if __name__ == "__main__":
    asyncio.run(run_simulation())
