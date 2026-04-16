"""
Match SQLAlchemy model.
"""
from sqlalchemy import Column, String, Float, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    MATCHED = "matched"
    REJECTED = "rejected"
    SHORTLISTED = "shortlisted"
    INTERVIEWED = "interviewed"
    HIRED = "hired"


class Match(Base, TimestampMixin):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, index=True)
    cv_id = Column(String, ForeignKey("cvs.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    cross_encoder_score = Column(Float)   # Raw Cross-Encoder output
    rrf_score = Column(Float)             # Hybrid search RRF score
    details = Column(JSON)                # Full explanation, skill gaps, etc.
    matching_skills = Column(JSON)        # Skills that matched
    missing_skills = Column(JSON)         # Skills the candidate lacks
    status = Column(
        SAEnum(MatchStatus, values_callable=lambda x: [e.value for e in x]),
        default=MatchStatus.PENDING,
        nullable=False,
    )

    cv = relationship("CV", back_populates="matches")
    job = relationship("Job")
