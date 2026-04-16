from enum import Enum

class JobPlatform(str, Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"

class MatchStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    REJECTED = "rejected"
    SHORTLISTED = "shortlisted"

SUPPORTED_FILE_TYPES = [".pdf", ".docx", ".txt"]
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
MAX_CV_SIZE_MB = 10
