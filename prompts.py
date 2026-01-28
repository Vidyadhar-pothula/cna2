# System Prompts for Entity Extraction

UNIFIED_EXTRACTION_PROMPT = """
    Context:
    \"\"\"
    {chunk}
    \"\"\"

    Task:
    Extract ALL of the following control system entities from the context into a single JSON object.

    Definitions & Rules:

    1. EQUIPMENT (Physical Assets):
       - Vessels, valves, pumps, sensors.
       - EXTRACT REAL IDs: If text says "Pump P-101", extract id="P-101", name="Pump".
       - NO INVENTED IDs.

    2. PARAMETERS (Configurable Values):
       - Setpoints, limits, constants (C1, C2), timers, deadbands.
       - EXTRACT REAL IDs (e.g., "Parameter P-101").

    3. VARIABLES (Measured Values):
       - pH, Flow, Weight, Conductivity which CHANGE during operation.
       - NO Constants.

    4. CONDITIONS (Triggers):
       - Causes/Logic (IF, WHEN, ABOVE, BELOW).
       - Capture only the TRIGGER.

    5. ACTIONS (Responses):
       - System effects (opens, closes, adds, alarms).
       - Capture only the RESPONSE.

    CRITICAL: Extract ONLY from the "Context" above. Do NOT include examples from these definitions.

    Output JSON Format:
    {{
      "equipment": [ {{ "id": "...", "name": "...", "description": "..." }} ],
      "parameters": [ {{ "id": "...", "name": "...", "description": "..." }} ],
      "variables":  [ {{ "id": "...", "name": "...", "description": "..." }} ],
      "conditions": [ {{ "name": "...", "description": "..." }} ],
      "actions":    [ {{ "name": "...", "description": "..." }} ]
    }}
"""
