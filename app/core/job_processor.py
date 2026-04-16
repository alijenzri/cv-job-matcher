"""
Job Processor: cleans and extracts structured data from job descriptions.
Uses LLM for intelligent skill/requirement extraction.
"""
import re
import json
import logging

logger = logging.getLogger(__name__)


class JobProcessor:
    def process(self, text: str) -> dict:
        """
        Process job description text: clean and extract key sections.
        """
        cleaned_text = self._clean_text(text)
        return {
            "text": cleaned_text,
            "raw_text": text,
            "metadata": {
                "length": len(cleaned_text),
                "word_count": len(cleaned_text.split())
            }
        }

    def extract_requirements(self, text: str) -> dict:
        """
        Use LLM to extract structured requirements from a job description.
        Returns skills, experience requirements, qualifications, etc.
        """
        from app.core.llm import LLMService

        llm = LLMService()

        prompt = f"""Extract the following fields from the job description below:
- required_skills (list of strings - technical/hard skills)
- preferred_skills (list of strings - nice-to-have skills)
- min_experience_years (integer or null)
- education_level (string: "bachelor", "master", "phd", or null)
- certifications (list of strings)
- key_responsibilities (list of strings - top 5)

Job Description:
{text[:4000]}

Output JSON only."""

        system_prompt = "You are an expert job description parser. Output strictly valid JSON."

        json_response = llm.generate_text(prompt, system_prompt)

        # Clean code blocks if present
        if "```json" in json_response:
            json_response = json_response.split("```json")[1].split("```")[0].strip()
        elif "```" in json_response:
            json_response = json_response.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(json_response)
        except json.JSONDecodeError:
            logger.error("Failed to parse job requirements JSON")
            return {"raw_text": text, "error": "Failed to parse JSON"}

    def _clean_text(self, text: str) -> str:
        """Remove extra whitespace and normalize text."""
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def parse(self, job_text: str) -> dict:
        """Wrapper for backward compatibility."""
        return self.process(job_text)
