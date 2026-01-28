# LayoutLMv3 Prototype

This directory contains a Python prototype for the **Text & Section Extractor** phase using LayoutLMv3.

## Prerequisites

1.  **Python 3.8+**
2.  **Poppler** (Required for `pdf2image` to convert PDFs)
    *   **Mac (Homebrew)**: `brew install poppler`
    *   **Linux**: `sudo apt-get install poppler-utils`
    *   **Windows**: Download binary and add to PATH.

## Setup

1.  Create a virtual environment (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Place a PDF file named `sample_document.pdf` in this directory.
2.  Run the extractor:
    ```bash
    python layoutlmv3_extractor.py
    ```

## Output

The script will:
1.  Load the `microsoft/layoutlmv3-base` model.
2.  Convert the PDF to an image.
3.  Emulate OCR (using mock data for this prototype).
4.  Run inference to classify tokens (EQUIPMENT, VARIABLE, etc.).
5.  Save the structured result to `output.json`.
