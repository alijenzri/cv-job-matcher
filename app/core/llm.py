"""
Production LLM Service using the modern google-genai SDK.
"""
import os
import json
import logging
import time
from google import genai
from google.genai import types
from app.config import settings
from dotenv import load_dotenv

# Force .env override to bypass invalid system-level keys
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model_id: str = "models/gemini-2.5-flash"):
        self.api_key = os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = model_id
        self._call_count = 0

    def generate_text(
        self,
        prompt: str,
        system_prompt: str = "You are a professional technical recruiter.",
        temperature: float = 0.3,
    ) -> str:
        """
        Generate text using the Gemini 2.x/3.x series.
        """
        try:
            start = time.perf_counter()
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=2048,
                )
            )
            elapsed = time.perf_counter() - start
            self._call_count += 1
            
            result = response.text.strip()
            logger.info(f"LLM call #{self._call_count} ({self.model_id}) successful in {elapsed:.2f}s")
            return result
        except Exception as e:
            print(f"DEBUG: LLM FAILED: {e}")
            logger.error(f"LLM generation failed for {self.model_id}: {e}")
            return ""

    def generate_structured_json(self, prompt: str, system_prompt: str = None) -> str:
        if system_prompt is None:
            system_prompt = "You are an expert data analyst. Return ONLY strictly valid JSON."
        
        return self.generate_text(
            prompt,
            system_prompt=system_prompt,
            temperature=0.1
        )

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return len(text) // 4
