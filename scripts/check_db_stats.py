import os
import sys
import logging
from app.database.vector_db import VectorDB
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.ERROR)

def check_stats():
    try:
        db = VectorDB()
        stats = db.get_stats()
        print("\n" + "="*40)
        print("DATABASE STATISTICS")
        print("="*40)
        print(f"Total Jobs in DB: {stats.get('job_count', 0)}")
        print(f"Total CVs in DB:  {sum(stats.get('cv_stats', {}).values())}")
        if stats.get('cv_stats'):
            print("\nCV Status Breakdown:")
            for status, count in stats.get('cv_stats', {}).items():
                print(f" - {status}: {count}")
        print("="*40 + "\n")
        db.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    check_stats()
