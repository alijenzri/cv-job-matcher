import os
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title

class CVProcessor:
    def process(self, file_path: str):
        """
        Uses unstructured.io to robustly parse the document and extract text.
        This provides much cleaner extraction than basic pdfplumber.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Partition handles PDF, DOCX, TXT, HTML automatically
            elements = partition(filename=file_path)
            
            # Chunking by title creates logical blocks of text (e.g. grouped by header)
            chunks = chunk_by_title(elements)
            
            # Reconstruct clean text from chunks
            clean_text = "\n\n".join([str(chunk) for chunk in chunks])
            
            return {
                "text": clean_text,
                "metadata": {
                    "source": file_path,
                    "chunk_count": len(chunks)
                }
            }
        except Exception as e:
            print(f"Extraction failed with unstructured, falling back: {e}")
            raise ValueError(f"Failed to process file: {file_path}")

    def extract_structured_data(self, text: str):
        """
        Uses LLM to extract structured data (Skills, Experience, etc.) from CV text.
        """
        from app.core.llm import LLMService 
        # Lazy import to avoid circular dependency if any, strictly usually not needed here but good practice if structure is complex
        # efficient to init LLMService here or dependency inject it in __init__
        # For this refactor, let's inject it or instantiate it. 
        # Ideally, CVProcessor should receive LLMService.
        
        llm = LLMService()
        
        system_prompt = "You are an expert CV Parser. Output strictly valid JSON."
        prompt = f"""
        Extract the following fields from the resume text below:
        - name (string)
        - email (string)
        - phone (string)
        - skills (list of strings)
        - work_experience (list of objects with 'title', 'company', 'duration', 'description')
        - education (list of objects with 'degree', 'institution', 'year')
        - summary (string)

        Resume Text:
        {text[:4000]} 
        
        Output JSON only.
        """
        
        json_response = llm.generate_text(prompt, system_prompt)
        
        import json
        import logging
        logger = logging.getLogger(__name__)

        # Clean code blocks if present
        if "```json" in json_response:
            json_response = json_response.split("```json")[1].split("```")[0].strip()
        elif "```" in json_response:
            json_response = json_response.split("```")[1].split("```")[0].strip()
            
        # Robustly find the JSON object by looking for the first { and last }
        start_idx = json_response.find('{')
        end_idx = json_response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            json_response = json_response[start_idx:end_idx + 1]
            try:
                return json.loads(json_response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON after extraction: {e}")
        else:
            logger.error("No JSON object ({...}) found in the LLM response.")
            
        return {
            "name": "Unknown",
            "email": "",
            "skills": [],
            "summary": "Extraction Failed - Raw parsing error.",
            "raw_text": text, 
            "error": "Failed to parse JSON"
        }