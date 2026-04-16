"""
CV SQLAlchemy model.
"""
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class CVStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class CV(Base, TimestampMixin):
    __tablename__ = "cvs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String)
    file_hash = Column(String(64), unique=True, nullable=True, index=True)  # SHA-256 dedup
    parsed_content = Column(JSON)   # Stores extracted text and metadata
    skills = Column(JSON)           # Extracted skills list
    summary = Column(Text)          # LLM-generated summary
    status = Column(
        SAEnum(CVStatus, values_callable=lambda x: [e.value for e in x]),
        default=CVStatus.PENDING,
        nullable=False,
    )

    user = relationship("User", back_populates="cvs")
    matches = relationship("Match", back_populates="cv")
