"""
Unit tests for core engine components.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestCVProcessor:
    def test_process_file_not_found(self):
        from app.core.cv_processor import CVProcessor
        processor = CVProcessor()
        with pytest.raises(FileNotFoundError):
            processor.process("/nonexistent/path.pdf")


class TestJobProcessor:
    def test_clean_text(self):
        from app.core.job_processor import JobProcessor
        processor = JobProcessor()
        result = processor.process("  Hello   World  \n\n  Test  ")
        assert result["text"] == "Hello World Test"
        assert result["metadata"]["word_count"] == 3

    def test_parse_backward_compat(self):
        from app.core.job_processor import JobProcessor
        processor = JobProcessor()
        result = processor.parse("Test job description")
        assert "text" in result
        assert result["text"] == "Test job description"


class TestEmbeddings:
    def test_get_embedding_returns_list(self):
        from app.ml.utils.embeddings import get_embedding
        embedding = get_embedding("test text for embedding")
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # MiniLM-L6-v2 dimension

    def test_get_embeddings_batch(self):
        from app.ml.utils.embeddings import get_embeddings_batch
        texts = ["first text", "second text", "third text"]
        embeddings = get_embeddings_batch(texts)
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

    def test_get_embeddings_batch_empty(self):
        from app.ml.utils.embeddings import get_embeddings_batch
        result = get_embeddings_batch([])
        assert result == []


class TestMatcher:
    def test_matcher_init(self):
        from app.core.matcher import Matcher
        matcher = Matcher()
        assert matcher.cross_encoder is not None

    @pytest.mark.asyncio
    async def test_match_single(self):
        from app.core.matcher import Matcher
        matcher = Matcher()
        result = await matcher.match(
            "Python developer with 5 years experience",
            "Looking for senior Python developer"
        )
        assert "score" in result
        assert isinstance(result["score"], float)

    @pytest.mark.asyncio
    async def test_match_batch_empty(self):
        from app.core.matcher import Matcher
        matcher = Matcher()
        result = await matcher.match_batch([], "some job")
        assert result == []

    @pytest.mark.asyncio
    async def test_match_batch(self):
        from app.core.matcher import Matcher
        matcher = Matcher()
        cv_texts = [
            "Python developer with FastAPI experience",
            "Java developer with Spring Boot experience",
            "Data scientist with ML expertise"
        ]
        results = await matcher.match_batch(cv_texts, "Senior Python Developer needed")
        assert len(results) == 3
        assert all("score" in r for r in results)
