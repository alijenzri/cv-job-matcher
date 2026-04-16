"""
Job SQLAlchemy model.
"""
from sqlalchemy import Column, String, Text, JSON, Float
from app.models.base import Base, TimestampMixin


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    company = Column(String, index=True)
    location = Column(String)
    description = Column(Text)
    requirements = Column(JSON)       # Structured requirements list
    required_skills = Column(JSON)    # LLM-extracted required skills
    preferred_skills = Column(JSON)   # LLM-extracted preferred skills
    salary = Column(String)
    job_type = Column(String)         # Full-time, Part-time, Contract
    platform = Column(String)         # linkedin, indeed, glassdoor, manual
    original_url = Column(String)
    scrape_quality = Column(Float)    # 0-1 confidence score from scraper
