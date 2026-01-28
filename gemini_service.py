
import google.generativeai as genai
import json
import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def extract_entities(pdf_path, api_key):
    """
    Extracts structured entities from the PDF using Gemini API.
    Returns a dictionary with keys: equipment, parameters, variables, conditions, actions.
    """
    if not api_key:
        raise ValueError("API Key is missing.")

    text_content = extract_text_from_pdf(pdf_path)
    if not text_content:
        raise ValueError("Failed to extract text from PDF.")

    genai.configure(api_key=api_key)
    
    # Use flash for speed, or pro for better reasoning. Flash is usually sufficient for extraction.
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an expert Control Systems Engineer.
    Read the following Control Narrative document content carefully.
    
    Your task is to extract exactly 5 specific tables of information into a valid JSON object.
    
    The 5 categories are:
    1. **Equipment**: Identify all equipment mentioned. (Note: The user might refer to this as 'parameters' sometimes, but look for physical equipment tags like tanks, pumps, valves, etc.).
    2. **Parameters**: Control parameters, setpoints, limits, etc.
    3. **Variables**: Process variables (PV), manipulated variables (MV), etc.
    4. **Conditions**: Logic conditions, interlocks, permissive states.
    5. **Actions**: Control actions, valve openings/closings, pump starts/stops, alarms.

    Return ONLY a raw JSON string (no markdown formatting, no code blocks) with the following structure:
    {{
      "equipment": [ {{ "id": "...", "description": "..." }}, ... ],
      "parameters": [ {{ "id": "...", "description": "..." }}, ... ],
      "variables": [ {{ "id": "...", "description": "..." }}, ... ],
      "conditions": [ {{ "id": "...", "description": "..." }}, ... ],
      "actions": [ {{ "id": "...", "description": "..." }}, ... ]
    }}

    If an ID is not explicitly present, infer a reasonable short ID or use the name.
    
    Document Content:
    {text_content}
    """

    try:
        response = model.generate_content(prompt)
        
        # Clean up response if it contains markdown code blocks
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        return json.loads(clean_text)
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Return empty structure on error to prevent frontend crash
        return {
            "equipment": [],
            "parameters": [],
            "variables": [],
            "conditions": [],
            "actions": [],
            "error": str(e)
        }
