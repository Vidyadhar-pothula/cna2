import os
import sys
from dotenv import load_dotenv
from langchain_community.llms import Ollama
sys.path.append(os.path.join(os.getcwd(), 'ml_prototype'))
from ml_prototype.extraction_agents import ExtractionAgent

load_dotenv()
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "phi3:mini")

def test_extraction():
    llm = Ollama(model=EXTRACTION_MODEL, temperature=0.1)
    agent = ExtractionAgent(llm)
    
    test_text = "If discharge pressure (PT-101) exceeds 12bar, shut down pump P-101."
    print(f"Testing with text: {test_text}")
    
    # We want to see the RAW response too
    full_prompt = agent.get_prompt(test_text, {})
    print("--- FULL PROMPT ---")
    print(full_prompt)
    print("--- END PROMPT ---")
    
    response = llm.invoke(full_prompt, stop_sequences=["###", "```"])
    print("--- RAW RESPONSE ---")
    print(response)
    print("--- END RAW RESPONSE ---")
    
    result = agent.extract(test_text, {})
    print("--- PARSED RESULT ---")
    print(result)

if __name__ == "__main__":
    test_extraction()
