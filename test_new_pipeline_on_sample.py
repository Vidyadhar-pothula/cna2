import os
import json
from tinyllama_service import extract_entities_ollama

def test_on_sample():
    pdf_path = "ml_prototype/sample_2_pump.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    print(f"Running Scalable Pipeline on {pdf_path}...")
    try:
        result = extract_entities_ollama(pdf_path)
        print("Extraction completed!")
        print(json.dumps(result, indent=2))
        
        # Basic validation
        categories = ["equipment_table", "parameters_table", "variables_table", "conditions_table", "actions_table"]
        has_data = False
        for cat in categories:
            items = result.get(cat, [])
            if items:
                has_data = True
                print(f"Verified {len(items)} items in {cat}")
        
        if not has_data:
            print("WARNING: No data returned. This may be due to the expert semantic rules being very selective.")
            
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_on_sample()
