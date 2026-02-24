
import json
import re
import uuid
import os
import sys
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from pypdf import PdfReader

# Add current directory to path so ml_prototype is discoverable as a package
sys.path.append(os.path.dirname(__file__))
from ml_prototype.pipeline_manager import PipelineManager
# Fallback service
from gemini_service import extract_entities as gemini_extract

# Load ENV
load_dotenv()
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "phi3:mini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def extract_entities_ollama(pdf_path):
    """
    Entry point for the Scalable Agentic Pipeline with Gemini Fallback.
    """
    print(f"=== Starting Scalable Pipeline: {pdf_path} ===")
    
    # 1. Read PDF
    print(f"--- EXTRACTING ENTITIES FROM: {pdf_path} ---")
    text = ""
    try:
        import fitz # Use PyMuPDF for better reliability in industrial docs
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        print(f"  [ERROR] Failed to read PDF {pdf_path} with fitz: {e}")
        return {"error": f"Failed to read PDF: {str(e)}"}

    # SCANNED DOCUMENT DETECTION
    # Low threshold: few chars but significant size = likely scanned.
    text_len = len(text.strip())
    # Only fallback if text is effectively non-existent AND we have a key
    is_scanned = text_len < 10 
    
    if is_scanned and GEMINI_API_KEY:
        print(f"  [!] Likely scanned PDF (text len: {text_len}). Falling back to Gemini...")
        return gemini_extract(pdf_path, GEMINI_API_KEY)
    elif is_scanned and not GEMINI_API_KEY:
        print(f"  [!] Scanned PDF detected but no GEMINI_API_KEY. Attempting local scan anyway...")

    print(f"  -> Read {text_len} characters. Starting pipeline...")
    
    # 2. Initialize and run the new pipeline
    try:
        # Tuning for stability and speed
        llm = Ollama(model=EXTRACTION_MODEL, temperature=0.1)
        manager = PipelineManager(llm)
        result = manager.run_pipeline(text)
        
        # AUGMENTATION STRATEGY: Combine LLM results with Regex results
        # This ensures we get the 80% reasoning + the 20% reliable tag discovery
        summary = manager.context_builder.get_summary()
        
        # Merge Regex Equipment
        existing_eq_ids = {str(e.get("id", "")).upper() for e in result.get("equipment_table", [])}
        for eq_id in summary.get("equipment", []):
            if eq_id.upper() not in existing_eq_ids:
                result["equipment_table"].append({"id": eq_id, "name": eq_id, "description": "Reliably identified via scan"})
        
        # Merge Regex Variables
        existing_var_ids = {str(v.get("id", "")).upper() for v in result.get("variables_table", [])}
        for var_id in summary.get("variables", []):
            if var_id.upper() not in existing_var_ids:
                result["variables_table"].append({"id": var_id, "name": var_id, "description": "Reliably identified via scan"})

        counts = {k: len(result.get(k, [])) for k in ["equipment_table", "variables_table", "parameters_table", "conditions_table", "actions_table"]}
        print(f"  -> Pipeline finished. Augmented Results: {counts}")
        
        return result
    except Exception as e:
        import traceback
        print(f"  [CRITICAL ERROR] Pipeline failed: {e}")
        traceback.print_exc()
        return {"error": f"Pipeline internal error: {str(e)}"}

# Backward compatibility for app.py
class AgenticPipeline:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def run(self):
        return extract_entities_ollama(self.pdf_path)
