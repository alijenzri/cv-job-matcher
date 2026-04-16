import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_db():
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='alijenzri',
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'cv_matcher_db'")
        exists = cur.fetchone()
        if not exists:
            cur.execute('CREATE DATABASE cv_matcher_db')
            print("Database created successfully")
        else:
            print("Database already exists")
            
        cur.close()
        conn.close()
        
        # Connect to the new database to enable pgvector extension
        conn = psycopg2.connect(
            dbname='cv_matcher_db',
            user='postgres',
            password='alijenzri',
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        try:
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
            print("pgvector extension enabled")
        except Exception as e:
            print(f"Error enabling pgvector: {e}")
            print("You may need to install pgvector on your PostgreSQL server.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_db()
