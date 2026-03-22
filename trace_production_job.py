import os
import sys
import json
from tinyllama_service import extract_entities_ollama  # type: ignore # pylint: disable=import-error

def trace_job(pdf_path):
    print(f"=== TRACING PRODUCTION PIPELINE FOR: {pdf_path} ===")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    # 1. Run Extraction
    print("\n--- PHASE 1: Running Extraction via tinyllama_service ---")
    result = extract_entities_ollama(pdf_path)
    
    if "error" in result:
        print(f"!!! EXTRACTION ERROR: {result['error']}")
        return

    # 2. Inspect Normalized Tables
    print("\n--- PHASE 2: Inspecting Extraction Results ---")
    keys = ["equipment_table", "variables_table", "parameters_table", "conditions_table", "actions_table", "unified_control_table"]
    
    total_found = 0
    for k in keys:
        count = len(result.get(k, []))
        print(f"  {k:22}: {count} items")
        total_found += count
        if count > 0:
            print(f"    - First item: {result[k][0]}")

    if total_found == 0:
        print("\n[CRITICAL] No entities were extracted. Check the LLM response above.")
    else:
        print(f"\n[SUCCESS] Extracted {total_found} items in total.")
    
    # 3. Inspect Pseudocode
    if result.get("pseudocode") and len(result["pseudocode"]) > 50:
        print("\n--- PHASE 3: Pseudocode Generated ---")
        print(result["pseudocode"][:200] + "...")
    else:
        print("\n--- PHASE 3: Pseudocode missing or too short ---")

if __name__ == "__main__":
    # Test on a known sample first
    sample = "ml_prototype/sample_2_pump.pdf"
    trace_job(sample)
