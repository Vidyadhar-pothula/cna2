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
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if i == 0:
                 print("===== STEP 4: VERIFY PDF LOADER OUTPUT (Page 1) =====")
                 print(page_text)
                 print("=====================================================")
            text_content += page_text + "\n"
            
        if not text_content.strip():
            print("CRITICAL ERROR: PDF Text extraction returned empty string!")
            return {"error": "PDF text extraction failed (empty)"}
            
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
    
    # SINGLE-PASS BALANCED EXTRACTION
    from prompts import BALANCED_SYSTEM_PROMPT
    
    llm = Ollama(model=TINYLLAMA_MODEL, temperature=0.0)

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1}/{len(chunks)} ---")
        
        # Construct the Prompt (System + Chunk)
        # LangChain just concatenates, no rephrasing
        final_prompt = f"""{BALANCED_SYSTEM_PROMPT}\n\nDATA TO EXTRACT:\n{chunk}"""

        print(f"   -> Invoking Phi-3 (Balanced Pass)...")
        
        # RETRY LOOP (Max 1 retry for Anti-Collapse)
        max_retries = 1
        attempt = 0
        valid_extraction = False
        
        while attempt <= max_retries:
            try:
                raw_output = llm.invoke(final_prompt)
                parsed = extract_json_from_text(raw_output)
                
                if parsed and isinstance(parsed, dict):
                    # Check for "Collapse" (Skewed to Conditions only)
                    eq_count = len(parsed.get('equipment', []))
                    param_count = len(parsed.get('parameters', []))
                    cond_count = len(parsed.get('conditions', []))
                    
                    # Heuristic: If we have conditions but NO equipment/parameters, it might be collapsed.
                    if cond_count > 0 and eq_count == 0 and param_count == 0 and attempt < max_retries:
                        print(f"   WARNING: Detected potential 'Conditions-Only' collapse. Retrying (Attempt {attempt+1}/{max_retries})...")
                        attempt += 1
                        continue # Retry with same prompt
                    
                    # If we got here, result is either balanced or we ran out of retries
                    valid_extraction = True
                    
                    # Merge into aggregated data
                    for category in ["equipment", "parameters", "variables", "conditions", "actions"]:
                        items = parsed.get(category, [])
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    # Standard Validation
                                    name = (item.get("name") or "").strip()
                                    desc = (item.get("description") or "").strip()
                                    doc_id = (item.get("id") or "").strip()
                                    
                                    if not name or len(name) < 2: continue
                                    
                                    item_data = {"name": name, "description": desc}
                                    if category in ["equipment", "parameters", "variables"]:
                                        item_data["id"] = doc_id
                                        
                                    aggregated_data[category].append(item_data)
                    break # Exit retry loop
                else:
                    # JSON parse failed
                    print(f"   Warning: valid JSON not found in attempt {attempt}.")
                    attempt += 1
                    
            except Exception as e:
                print(f"    Error in extraction attempt {attempt}: {e}")
                attempt += 1
                
        if not valid_extraction:
            print("   Failed to extract valid data for chunk after retries.")

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
