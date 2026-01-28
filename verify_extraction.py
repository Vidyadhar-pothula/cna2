import sys
import os

# Add path
sys.path.append(os.getcwd())

from tinyllama_service import extract_entities_ollama

# Use the existing test file
pdf_path = "test_narrative.pdf"

if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} not found.")
    sys.exit(1)

print(f"Testing extraction on {pdf_path}...")
result = extract_entities_ollama(pdf_path)

import json
print(json.dumps(result, indent=2))
