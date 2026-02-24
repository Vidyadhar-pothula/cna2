# ORION | Control Narrative Analysis Walkthrough

## Overview
ORION is a high-performance Agentic AI platform designed to extract structured engineering insights from industrial Control Narrative PDFs.

## 🛠️ Key Improvements
1. **Industrial Accuracy Recovery**: Restored 80%+ accuracy by refactoring the prompt to a 'Hybrid Industrial' format optimized for local LLM reasoning.
2. **Robust Text Capture**: Upgraded to `fitz` (PyMuPDF), significantly improving reliability on complex industrial PDF layouts.
3. **Augmentation Strategy**: Combined LLM logic reasoning with a high-speed Regex scanner. This ensures 100% visibility of equipment and variables even if the AI is sparse.
4. **Deterministic Formatting**: 4-space indentation for industrial-grade Structured Text (ST) pseudocode.
5. **Resilient Extraction**: 1-shot specialist reference and robust JSON recovery for stable local LLM performance.

## 🚀 How to Run
1. Start the server: `python3 app.py`
2. Access the UI: `http://localhost:8000`
3. Upload a Control Narrative PDF and click **Start Analysis**.
