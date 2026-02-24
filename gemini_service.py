
import google.generativeai as genai
import json
import os
import time

def extract_text_from_pdf(pdf_path):
    """Fallback text extraction if Gemini File API fails."""
    text = ""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except:
        return ""

def extract_entities(pdf_path, api_key):
    """
    Extracts structured entities from the PDF using Gemini 2.0 Flash.
    Handles scanned documents via File API and text documents via text fallback.
    """
    if not api_key:
        raise ValueError("API Key is missing.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Shared prompt instruction
    instruction = """
    ACT AS: Professional Industrial Control Systems Engineer.
    TASK: Extract 5 categories: equipment, parameters, variables, conditions, actions.
    JSON FORMAT:
    {
      "equipment": [ {"id": "ID", "name": "Name", "description": "Desc"} ],
      "parameters": [ {"id": "ID", "name": "Name", "description": "Desc"} ],
      "variables": [ {"id": "ID", "name": "Name", "description": "Desc"} ],
      "conditions": [ {"id": "ID", "name": "Name", "description": "Desc"} ],
      "actions": [ {"id": "ID", "name": "Name", "description": "Desc"} ]
    }
    """

    try:
        # PRIMARY: Gemini File API (Vision/OCR for scanned PDFs)
        try:
            print(f"  [Gemini] Attempting File API Upload: {pdf_path}...")
            sample_file = genai.upload_file(path=pdf_path, display_name="Control Narrative")
            
            while sample_file.state.name == "PROCESSING":
                time.sleep(1)
                sample_file = genai.get_file(sample_file.name)

            if sample_file.state.name == "FAILED":
                raise ValueError("File API Failed")

            print(f"  [Gemini] Running Vision Extraction...")
            response = model.generate_content([sample_file, instruction])
            genai.delete_file(sample_file.name)
            
        except Exception as file_api_err:
            print(f"  [Gemini] File API failed ({file_api_err}). Falling back to Text-Based Gemini...")
            # SECONDARY: Text-based extraction (if File API is blocked/leaked)
            text_content = extract_text_from_pdf(pdf_path)
            if not text_content or len(text_content.strip()) < 5:
                raise ValueError("No text extractable for secondary fallback.")
            
            response = model.generate_content([instruction, f"DOCUMENT TEXT:\n{text_content}"])

        # Final Parse
        resp_text = response.text.strip()
        if "```json" in resp_text:
            resp_text = resp_text.split("```json")[-1].split("```")[0].strip()
        elif "```" in resp_text:
            resp_text = resp_text.split("```")[-1].split("```")[0].strip()
            
        raw_data = json.loads(resp_text)
        
        return {
            "equipment_table": raw_data.get("equipment", []),
            "variables_table": raw_data.get("variables", []),
            "parameters_table": raw_data.get("parameters", []),
            "conditions_table": raw_data.get("conditions", []),
            "actions_table": raw_data.get("actions", []),
            "unified_control_table": [],
            "pseudocode": "// Generated via Gemini Fallback"
        }
        
    except Exception as e:
        print(f"  [ERROR] Gemini Fallback Failed: {e}")
        return {"error": str(e)}
