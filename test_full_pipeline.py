import os
import sys
from dotenv import load_dotenv
from langchain_community.llms import Ollama
import fitz

# Add current directory to path
sys.path.append(os.getcwd())
from ml_prototype.pipeline_manager import PipelineManager

load_dotenv()
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "phi3:mini")

def test_full_pipeline():
    pdf_path = "test_narrative.pdf"
    print(f"Testing full pipeline with: {pdf_path}")
    
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    
    print(f"Read {len(text)} characters.")
    print("--- TEXT CONTENT ---")
    print(text)
    print("--- END TEXT ---")
    
    llm = Ollama(model=EXTRACTION_MODEL, temperature=0.1)
    manager = PipelineManager(llm)
    
    print("Running pipeline...")
    result = manager.run_pipeline(text)
    
    import json
    print("--- PIPELINE RESULT ---")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_full_pipeline()
