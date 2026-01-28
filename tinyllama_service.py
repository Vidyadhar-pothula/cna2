import json
import re
import time
from langchain_community.llms import Ollama

# === Configuration ===
TINYLLAMA_MODEL = "phi3:mini"

def extract_json_from_text(text):
    """
    Attempts to extract a JSON object from a string using json_repair.
    """
    # 1. Cleaning: Remove Markdown code blocks if present
    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*', '', text) # Remove closing ticks
    
    # 2. Try json_repair (Most robust)
    try:
        import json_repair
        decoded = json_repair.repair_json(text, return_objects=True)
        if decoded:
             return decoded
    except ImportError:
        print("Warning: json_repair not installed. Falling back.")

    # 3. Try standard JSON extraction
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = text[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
        
    return None

def extract_entities_ollama(pdf_path):
    """
    Extracts entities from the PDF text using the local Phi-3-mini model.
    Uses a DETERMINISTIC 5-PASS PIPELINE with REAL ID EXTRACTION.
    """
    start_time = time.time()
    print(f"--- Starting Extraction for {pdf_path} using Phi-3-mini ---")

    # 1. Read Text from PDF
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
    except Exception as e:
        return {"error": f"PDF Reading Error: {str(e)}"}

    # 2. CHUNK TEXT (Strict Logic-Preserving)
    # Using RecursiveCharacterTextSplitter to respect sentence boundaries
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=250,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = text_splitter.split_text(text_content)
    except ImportError:
        # Fallback if langchain.text_splitter is not available
        print("RecursiveCharacterTextSplitter not found, using simple slicing.")
        CHUNK_SIZE = 1200
        OVERLAP = 250
        chunks = []
        if len(text_content) > CHUNK_SIZE:
             start = 0
             while start < len(text_content):
                end = min(start + CHUNK_SIZE, len(text_content))
                chunks.append(text_content[start:end])
                if end == len(text_content):
                    break
                start += CHUNK_SIZE - OVERLAP
        else:
             chunks = [text_content]

    print(f"Processing {len(chunks)} chunks using 5-Pass Real-ID Pipeline...")

    # 3. MULTI-PASS EXTRACTION LOOP
    aggregated_data = {
        "equipment": [], "parameters": [], "variables": [], "conditions": [], "actions": []
    }
    
    # Define the 5 Passes (With ID Extraction where applicable)
    passes = [
        {
            "category": "equipment",
            "json_key": "equipment",
            "prompt_template": """
    Context:
    \"\"\"
    {chunk}
    \"\"\"

    Task:
    Extract EQUIPMENT from the context.
    Definition: Physical assets (vessels, valves, pumps, sensors).
    
    RULES:
    1. EXTRACT REAL IDs: If the text says "SV01 Surge Vessel", extract id="SV01", name="Surge Vessel".
    2. NO INVENTED IDs: If no ID exists, leave "id" empty. Do NOT create "E-1".
    3. Use exact names from text.
    4. Controlled Interpretation: "Valve opens" -> Equipment="Valve".

    Output Format (JSON):
    {{
      "equipment": [ {{ "id": "<SV01 or empty>", "name": "<document Name>", "description": "<role>" }} ]
    }}
    """
        },
        {
            "category": "parameters",
            "json_key": "parameters",
            "prompt_template": """
    Context:
    \"\"\"
    {chunk}
    \"\"\"

    Task:
    Extract PARAMETERS from the context.
    Definition: Configurable values (Setpoints, Limits, Constants).
    
    RULES:
    1. EXTRACT REAL IDs: If text says "Parameter P-101", extract id="P-101".
    2. Polynomial constants (C1, C2) -> id="C1", name="Polynomial Constant".
    3. NO INVENTED IDs.
    4. "Mixing time", "Deadbands", "Tolerances" are PARAMETERS.

    Output Format (JSON):
    {{
      "parameters": [ {{ "id": "<C1 or empty>", "name": "<document Name>", "description": "<value/purpose>" }} ]
    }}
    """
        },
        {
            "category": "variables",
            "json_key": "variables",
            "prompt_template": """
    Context:
    \"\"\"
    {chunk}
    \"\"\"

    Task:
    Extract VARIABLES from the context.
    Definition: Measured or calculated process values (pH, Flow, Weight).
    
    RULES:
    1. EXTRACT REAL IDs if present (e.g., tags).
    2. EXCLUDE C1, C2 (Parameters).
    3. NO INVENTED IDs.

    Output Format (JSON):
    {{
      "variables": [ {{ "id": "<tag or empty>", "name": "<document Name>", "description": "<measurement>" }} ]
    }}
    """
        },
        {
            "category": "conditions",
            "json_key": "conditions",
            "prompt_template": """
    Context:
    \"\"\"
    {chunk}
    \"\"\"

    Task:
    Extract CONDITIONS (Triggers).
    Definition: Logic that triggers an action (IF, WHEN, ABOVE, BELOW).
    
    RULES:
    1. Capture the TRIGGER part only (e.g., "If Level > 80%").
    2. Do not include action.
    3. NO IDs for Conditions.

    Output Format (JSON):
    {{
      "conditions": [ {{ "name": "<short label>", "description": "<trigger logic>" }} ]
    }}
    """
        },
        {
            "category": "actions",
            "json_key": "actions",
            "prompt_template": """
    Context:
    \"\"\"
    {chunk}
    \"\"\"

    Task:
    Extract ACTIONS (Responses).
    Definition: What the system DOES (opens, closes, adds, alarms).
    
    RULES:
    1. Capture the RESPONSE only.
    2. Do not include condition.
    3. NO IDs for Actions.

    Output Format (JSON):
    {{
      "actions": [ {{ "name": "<action name>", "description": "<system response>" }} ]
    }}
    """
        }
    ]

    llm = Ollama(model=TINYLLAMA_MODEL, temperature=0.1)

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1}/{len(chunks)} ---")
        
        for p in passes:
            prompt = p["prompt_template"].format(chunk=chunk)
            
            try:
                raw_output = llm.invoke(prompt)
                parsed = extract_json_from_text(raw_output)
                
                if parsed and isinstance(parsed, dict):
                     items = parsed.get(p["json_key"], [])
                     if isinstance(items, list):
                         for item in items:
                             if isinstance(item, dict):
                                 # VALIDATION
                                 name = item.get("name", "").strip()
                                 desc = item.get("description", "").strip()
                                 doc_id = item.get("id", "").strip()
                                 
                                 # 1. Check for placeholders
                                 bad_words = [
                                     "<exact", "document name", "physical role", "parameter name", 
                                     "<SV01", "<C1", "<tag",
                                     "variable name", "short condition", "action name", "exact action", 
                                     "<verbatim", "verbatim text", "verbatim meaning", "exact logic", 
                                     "<verbatim trigger>", "<verbatim action>", "<exact response>",
                                     "<short label>", "<trigger logic>", "<system response>", "<measurement>",
                                     "<value or purpose>", "<role>"
                                 ]
                                 if any(bw.lower() in name.lower() for bw in bad_words) or any(bw.lower() in desc.lower() for bw in bad_words):
                                     continue # Skip placeholder
                                     
                                 # 2. Check for empty
                                 if not name or len(name) < 2:
                                     continue
                                     
                                 item_data = {
                                     "name": name,
                                     "description": desc
                                 }
                                 # Add ID only if category supports it and it exists
                                 if p["category"] in ["equipment", "parameters", "variables"]:
                                     if doc_id and not any(bw.lower() in doc_id.lower() for bw in bad_words):
                                         item_data["id"] = doc_id
                                     else:
                                         item_data["id"] = "" # Explicit empty string as requested

                                 aggregated_data[p["category"]].append(item_data)
            except Exception as e:
                print(f"    Error in pass {p['category']}: {e}")
                continue

    # 4. POST-PROCESSING (Deduplicate ONLY - NO AUTO ID)
    final_normalized = {}
    
    for cat in aggregated_data:
        unique_map = {}
        for item in aggregated_data[cat]:
             # Key for deduplication
             dedup_key = (item.get("name", "").lower() + "|" + item.get("description", "").lower())
             
             if dedup_key not in unique_map:
                 # NO AUTO-ID GENERATION
                 # We simply use what we extracted
                 unique_map[dedup_key] = item
        
        final_normalized[cat] = list(unique_map.values())
        print(f"Final {cat}: {len(final_normalized[cat])} items")

    print(f"Extraction Finished. Total chunks processed: {len(chunks)}")
    
    # Add dummy prompt for UI compatibility
    final_normalized["used_prompt"] = "Multi-pass Real-ID extraction utilized."
    
    return final_normalized
