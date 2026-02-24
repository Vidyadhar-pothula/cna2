import json
import re
import concurrent.futures
from typing import List, Dict

class ExtractionAgent:
    """
    Unified extraction agent based on the Industrial Control Logic Extraction Engine system role.
    Extracts all 5 categories (equipment, variables, parameters, conditions, actions) in a single pass.
    """
    def __init__(self, llm):
        self.llm = llm

    def get_prompt(self, chunk: str, global_context: Dict) -> str:
        return f"""### ROLE: Industrial Controls Engineer. Extract structured entity data.

### TRANSFORMATION RULES:
1. Conditions: Convert narrative to symbolic logic (e.g. "when pressure > 10bar").
2. Symbols allowed: > < >= <= == !=
3. IDs: Preserve original. If missing, generate EQP-###, VAR-###, etc.
4. Accuracy: Only extract what is explicitly stated. Do NOT summarize.
5. EXHAUSTIVE EXTRACTION: Extract EVERY piece of equipment, variable, parameter, condition, and action.
6. DESCRIPTIONS: Provide a detailed, meaningful description for every entity extracted. "No description" is NOT allowed.

### 1-SHOT EXAMPLE:
Input: "If discharge pressure (PT-101) exceeds 12bar, shut down pump P-101."
Output: {{
  "equipment": [{{ "id": "P-101", "name": "Pump", "description": "High-pressure discharge pump for the main system" }}],
  "variables": [{{ "id": "PT-101", "name": "Discharge Pressure", "description": "Pressure transmitter monitoring the discharge line" }}],
  "parameters": [{{ "id": "PAR-001", "name": "12bar", "description": "High-high pressure trip setpoint for pump safety" }}],
  "conditions": [{{ "id": "CND-001", "name": "PT-101 > 12bar", "description": "Condition where discharge pressure exceeds the safety limit" }}],
  "actions": [{{ "id": "ACT-001", "name": "P-101.Stop", "description": "Immediate shutdown of pump P-101" }}]
}}

### INPUT TEXT:
{chunk}

### RETURN ONLY VALID JSON:
"""

    def extract(self, chunk: str, global_context: Dict) -> Dict[str, List[Dict]]:
        full_prompt = self.get_prompt(chunk, global_context)
        
        try:
            # Removed stop_sequences that often truncate JSON if the model uses code blocks
            response = self.llm.invoke(full_prompt)
            resp_text = response.strip()
            
            # Robust JSON recovery: Find the first { and last }
            json_match = re.search(r'(\{.*\})', resp_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                # Ensure the JSON string is properly closed if it was truncated
                open_braces = json_str.count('{')
                close_braces = json_str.count('}')
                if open_braces > close_braces:
                    json_str += '}' * (open_braces - close_braces)
                elif close_braces > open_braces:
                    # Truncate to matching braces if possible
                    pass
                
                try:
                    data = json.loads(json_str)
                    required_keys = ["equipment", "variables", "parameters", "conditions", "actions"]
                    for key in required_keys:
                        if key not in data: data[key] = []
                    return data
                except json.JSONDecodeError:
                    print(f"Extraction JSON Decode error for chunk. Response snippet: {resp_text[:100]}...")
            
            return {k: [] for k in ["equipment", "variables", "parameters", "conditions", "actions"]}
        except Exception as e:
            print(f"Extraction error: {e}")
            return {k: [] for k in ["equipment", "variables", "parameters", "conditions", "actions"]}

class ParallelExtractionOrchestrator:
    def __init__(self, llm):
        self.agent = ExtractionAgent(llm)

    def run_parallel(self, chunks: List[str], global_context: Dict) -> Dict[str, List[Dict]]:
        """
        Runs unified extraction across chunks.
        """
        combined_results = {
            "equipment": [],
            "variables": [],
            "parameters": [],
            "conditions": [],
            "actions": []
        }
        
        # Aligned with the new prompt keys
        key_map = {
            "equipment": "equipment",
            "variables": "variables",
            "parameters": "parameters",
            "conditions": "conditions",
            "actions": "actions"
        }

        # Reduced workers to 1 to avoid overwhelming local Ollama which can cause quality drops
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future_to_chunk = {executor.submit(self.agent.extract, chunk, global_context): chunk for chunk in chunks}
            for future in concurrent.futures.as_completed(future_to_chunk):
                try:
                    chunk = future_to_chunk[future]
                    chunk_id = f"chunk_{chunks.index(chunk)}"
                    chunk_data = future.result()
                    for prompt_key, internal_key in key_map.items():
                        if prompt_key in chunk_data and isinstance(chunk_data[prompt_key], list):
                            for item in chunk_data[prompt_key]:
                                item["_chunk_id"] = chunk_id
                            combined_results[internal_key].extend(chunk_data[prompt_key])
                except Exception as e:
                    print(f"Chunk processing failed: {e}")
        
        return combined_results
