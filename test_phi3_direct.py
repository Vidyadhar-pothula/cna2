
from langchain_community.llms import Ollama
import json
import time

def test_phi3_direct():
    print("===== STEP 3: BYPASS PIPELINE WITH HARD-CODED TEST =====")
    
    # 1. Setup
    model_name = "phi3:mini"
    llm = Ollama(model=model_name, temperature=0.0)
    
    # 2. Hard-coded Prompt
    prompt_text = """
TEXT:
SV01 ProA Surge Vessel
SV02 Viral Inactivation Surge Vessel

TASK:
List all equipment mentioned in the TEXT.

OUTPUT JSON ONLY:
{
  "equipment": []
}
"""

    print(f"Model: {model_name}")
    print("Prompting...")
    
    try:
        start = time.time()
        response = llm.invoke(prompt_text)
        duration = time.time() - start
        
        print("\n===== RAW RESPONSE =====")
        print(response)
        print("========================")
        print(f"Duration: {duration:.2f}s")
        
        if "SV01" in response and "SV02" in response:
             print("\nSUCCESS: Model returned known entities.")
        else:
             print("\nFAILURE: Model did not return SV01/SV02.")
             
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")

if __name__ == "__main__":
    test_phi3_direct()
