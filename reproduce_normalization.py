import json
import sys

# The user's actual output from the debug view
raw_output = {
  "actions": [],
  "conditions": [
    {
      "command": "Open Valve",
      "description": "Logic Condition",
      "id": "COND"
    }
  ],
  "equipment": [
    {
      "actions": [],
      "conditions": [
        {
          "command": "Open Valve",
          "description": "Logic Condition",
          "id": "COND"
        }
      ],
      "description": "Equipment Name",
      "id": "V-101",
      "parameters": [
        {
          "condition": "If Level > 50%",
          "description": "Parameter Description",
          "id": "P-202",
          "value": 50
        }
      ],
      "variables": []
    }
  ],
  "parameters": [],
  "variables": []
}

def normalize_nested_output(data):
    normalized = {
        "equipment": [], "parameters": [], "variables": [], "conditions": [], "actions": []
    }
    
    # Key mapping specific to this model's quirks
    key_map = {
        "equipment": "equipment", "equipments": "equipment",
        "parameter": "parameters", "parameters": "parameters",
        "variable": "variables", "variables": "variables", 
        "condition": "conditions", "conditions": "conditions",
        "action": "actions", "actions": "actions"
    }

    def extract_recursively(obj):
        if isinstance(obj, dict):
            # Check if this node itself is a top-level category we want to inspect
            # But more importantly, check its children
            
            # If this dict looks like an entity (has 'id'), add it to the best guess category?
            # actually, usually the model puts them under keys.
            
            for k, v in obj.items():
                target_key = key_map.get(k.lower())
                
                if target_key:
                    # It's a known category list/item
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                # Add to main list
                                normalized[target_key].append(item)
                                # Recurse into this item to find nested stuff
                                extract_recursively(item)
                    elif isinstance(v, dict):
                         normalized[target_key].append(v)
                         extract_recursively(v)
                else:
                    # It's some other key, just recurse
                    extract_recursively(v)
                    
        elif isinstance(obj, list):
            for item in obj:
                extract_recursively(item)

    extract_recursively(data)
    
    # Remove top-level duplicates if any (simple id based)
    for cat in normalized:
        unique = {}
        for item in normalized[cat]:
            if "id" in item:
                unique[item["id"]] = item
        normalized[cat] = list(unique.values())

    return normalized

print("Original:")
print(json.dumps(raw_output, indent=2))
print("\nNormalized:")
result = normalize_nested_output(raw_output)
print(json.dumps(result, indent=2))
