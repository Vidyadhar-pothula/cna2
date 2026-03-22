import os
import sys
import warnings

# Suppress specific noisy warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="urllib3")
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# Standard Python imports resolve this directly from the project root
from langchain_ollama import OllamaLLM  # type: ignore # noqa: E402 # pylint: disable=import-error
from ml_prototype.pipeline_manager import PipelineManager  # type: ignore # noqa: E402 # pylint: disable=import-error

PRIMARY_MODEL = "qwen2.5:14b"
FALLBACK_MODEL = "llama3.1:8b"


def extract_entities_ollama(pdf_path: str) -> dict:
    """
    Entry point for the Semantic Agentic Pipeline using Local Ollama Models.
    No Gemini Fallback. No Regex Fallback. Pure Semantic Reasoning.
    """
    print(f"=== Starting Semantic Pipeline: {pdf_path} ===")

    # 1. Read PDF Text
    print(f"--- EXTRACTING TEXT FROM: {pdf_path} ---")
    text = ""
    try:
        import fitz  # type: ignore # pylint: disable=import-error
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        print(f"  [ERROR] Failed to read PDF {pdf_path} with fitz: {e}")
        return {"error": f"Failed to read PDF: {str(e)}"}

    text_len = len(text.strip())
    if text_len < 10:
        err_msg = (
            "PDF contains no readable text. Scanned PDFs are not supported "
            "in this local pipeline without an OCR pre-processor."
        )
        return {"error": err_msg}

    print(f"  -> Read {text_len} characters. Initializing LLMs...")

    # 2. Initialize Models
    try:
        # Use lower temperature for deterministic logic reasoning
        primary_llm = OllamaLLM(model=PRIMARY_MODEL, temperature=0.1)
        fallback_llm = OllamaLLM(model=FALLBACK_MODEL, temperature=0.1)

        manager = PipelineManager(primary_llm, fallback_llm)
        result = manager.run_pipeline(text)

        return result
    except Exception as e:
        error_msg = str(e)
        print(f"  [ERROR] Pipeline safely caught failure: {error_msg}")
        return {"error": f"Pipeline internal error: {error_msg}"}


class AgenticPipeline:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def run(self):
        return extract_entities_ollama(self.pdf_path)
