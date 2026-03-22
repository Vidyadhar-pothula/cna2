import json
from typing import List, Dict, Any
from .agents import SemanticAgentBase  # type: ignore # pylint: disable=import-error

class SemanticNormalizationEngine(SemanticAgentBase):
    """
    Handles schema enforcement, deduplication, and conflict resolution semantically.
    """
    def __init__(self, primary_llm, fallback_llm):
        super().__init__(primary_llm, fallback_llm)  # type: ignore

    def normalize(self, raw_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Takes raw extracted entity lists from multiple sections (or single section) 
        and semantically merges duplicates, fixes naming variations, and enforces schema.
        """
        # To avoid context limits, we normalize per category
        normalized_data = {cat: [] for cat in raw_results.keys()}
        
        for category, items in raw_results.items():
            if not items:
                continue
                
            prompt = f"""
            ACT AS: Master Data Manager for Industrial Systems.
            TASK: Semantically normalize the following list of extracted '{category}' entities.
            
            RULES:
            1. Merge exact or semantic duplicates into a single entry.
            2. Resolve naming variations to a consistent standardized name.
            3. Ensure every entry strictly has the keys: "id", "name", "description".
            4. If an entity is clearly a hallucination or dummy placeholder, remove it.
            
            INPUT DATA: {json.dumps(items)}
            
            OUTPUT FORMAT (JSON ONLY):
            {{
                "normalized_{category}": [
                    {{
                        "id": "...",
                        "name": "...",
                        "description": "..."
                    }}
                ]
            }}
            
            Return ONLY valid JSON.
            """
            
            def validate(data):
                key = f"normalized_{category}"
                if key not in data or not isinstance(data[key], list):
                    raise ValueError(f"Missing '{key}' array in normalization.")
                    
            try:
                result = self._invoke_with_fallback(prompt, schema_check=validate)
                normalized_data[category] = result.get(f"normalized_{category}", [])
            except Exception as e:
                print(f"[NORMALIZATION] Semantic normalization failed for {category}: {e}")
                # Fallback to literal pass-through if all models fail
                normalized_data[category] = items
                
        return normalized_data
