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
        return f"""### ROLE: Senior Industrial Controls Engineer & Logic Expert.
Extract ALL technical entities from the provided Industrial Control Narrative text into structured JSON.

### EXTRACTION CATEGORIES:
1. equipment: All physical hardware (Pumps, Valves, Tanks, Sensors, PLCs).
2. variables: Process values (Level, Pressure, Flow) and Status/Commands.
3. parameters: Setpoints, limits, thresholds, and numerical constants.
4. conditions: Logical triggers and if-statements (e.g., "Level > 80%").
5. actions: Control outputs and resulting behaviors (e.g., "Open SV-101").

### CRITICAL RULES:
- If a specific ID is mentioned (e.g., PT-101), use it. Otherwise, invent a logical ID (EQP-001, VAR-001, etc.).
- ORIGINAL PHRASE: Capture the exact text fragment used to identify the entity (e.g., "P-101", "Level", "discharge pressure").
- DESCRIPTIONS: Provide a rich, professional description for every entity.
- LOGIC: Convert conditions into symbolic form (>, <, ==).
- FORMAT: RETURN ONLY THE JSON OBJECT. NO EXPLANATORY TEXT.

### EXTRACTION EXAMPLE:
Input: "Pump P-101 stops when the discharge pressure PT-101 reaches the high limit of 15bar."
Output: {{
  "equipment": [{{ "id": "P-101", "name": "Discharge Pump", "description": "Main system discharge pumping unit", "original_phrase": "Pump P-101" }}],
  "variables": [{{ "id": "PT-101", "name": "Discharge Pressure", "description": "Pressure transmitter on the discharge side of P-101", "original_phrase": "discharge pressure PT-101" }}],
  "parameters": [{{ "id": "PAR-101", "name": "15bar", "description": "High pressure safety trip setpoint", "original_phrase": "15bar" }}],
  "conditions": [{{ "id": "CND-101", "name": "PT-101 >= 15bar", "description": "Discharge pressure exceeds safely allowed operational limit", "original_phrase": "discharge pressure PT-101 reaches the high limit of 15bar" }}],
  "actions": [{{ "id": "ACT-101", "name": "P-101.Stop", "description": "Automatic shutdown of the discharge pump for protection", "original_phrase": "Pump P-101 stops" }}]
}}

### INPUT TEXT:
{chunk}

### STRICT JSON OUTPUT:
"""

    def extract(self, chunk: str, global_context: Dict) -> Dict[str, List[Dict]]:
        full_prompt = self.get_prompt(chunk, global_context)
        
        try:
            # Removed stop_sequences that often truncate JSON if the model uses code blocks
            response = self.llm.invoke(full_prompt)
            resp_text = response.strip()
            print(f"DEBUG: LLM RAW RESPONSE: {resp_text[:200]}...")
            
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
                except json.JSONDecodeError as de:
                    print(f"Extraction JSON Decode error: {de}")
                    print(f"DEBUG: FULL RAW RESPONSE STARTING:\n{resp_text}\nDEBUG: FULL RAW RESPONSE ENDING")
                    # Try a more aggressive cleanup if simple one failed
                    try:
                        # Remove anything before first { and after last }
                        start_idx = resp_text.find('{')
                        end_idx = resp_text.rfind('}')
                        if start_idx != -1 and end_idx != -1:
                            json_str = resp_text[start_idx:end_idx+1]
                            data = json.loads(json_str)
                            return data
                    except:
                        pass
            
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
