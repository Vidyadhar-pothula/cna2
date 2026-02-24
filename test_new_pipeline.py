import os
import json
from tinyllama_service import extract_entities_ollama

def test_pipeline():
    pdf_path = "test_narrative.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    print(f"Running extraction on {pdf_path}...")
    try:
        result = extract_entities_ollama(pdf_path)
        print("Extraction completed!")
        print(json.dumps(result, indent=2))
        
        # Basic validation
        categories = ["equipment", "parameters", "variables", "conditions", "actions"]
        has_data = False
        for cat in categories:
            items = result.get(cat, [])
            if items:
                has_data = True
                print(f"Verified {len(items)} items in {cat}")
        
        if not has_data:
            print("WARNING: No data returned in any category.")
            
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_pipeline()
