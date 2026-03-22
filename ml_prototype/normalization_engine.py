from typing import List, Dict, Set
import hashlib

class NormalizationEngine:
    """
    Handles schema enforcement, deduplication, and hallucination filtering.
    """
    def __init__(self):
        self.seen_hashes = set()

    def generate_hash(self, item: Dict) -> str:
        # Use ID and Name for hashing. Fallback to full content if ID is empty.
        id_val = str(item.get("id", "")).strip().upper()
        name_val = str(item.get("name", "")).strip().lower()
        
        if id_val:
            content = f"ID:{id_val}"
        else:
            content = f"NAME:{name_val}"
            
        return hashlib.md5(content.encode()).hexdigest()

    def normalize_item(self, item: Dict, category: str) -> Dict:
        """
        Enforces {id, name, description} schema.
        """
        clean_item = {
            "id": str(item.get("id", "")).strip() or "UNKNOWN",
            "name": str(item.get("name", "")).strip() or "Unnamed Entity",
            "description": str(item.get("description", "")).strip() or "No description provided"
        }
        
        # Hallucination check: If it looks like a generic LLM placeholder, flag it
        placeholders = ["placeholder", "tag1", "var1", "name1", "dummy"]
        if any(p in clean_item["name"].lower() for p in placeholders):
            return None # Drop potential hallucination
            
        # Optional: Category specific normalization (e.g., Conditions to symbolic form)
        if category == "conditions":
            clean_item["name"] = self._canonicalize_condition(clean_item["name"])
            
        return clean_item

    def _canonicalize_condition(self, condition_text: str) -> str:
        # Placeholder for complex symbolic conversion
        # For now, just basic cleanup. In a real system, use regex or small LLM pass.
        return condition_text.strip()

    def process_results(self, raw_results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        normalized_data = {cat: [] for cat in raw_results.keys()}
        self.seen_hashes.clear()
        
        for cat, items in raw_results.items():
            for item in items:
                # 1. Schema enforcement and cleaning
                clean_item = self.normalize_item(item, cat)
                if not clean_item:
                    continue
                    
                # 2. Deduplication
                item_hash = self.generate_hash(clean_item)
                if item_hash in self.seen_hashes:
                    # Optional: Merge descriptions or update with richer info
                    continue
                    
                self.seen_hashes.add(item_hash)
                normalized_data[cat].append(clean_item)
                
        return normalized_data
