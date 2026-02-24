import re
from typing import List, Dict, Tuple
from collections import Counter

class SemanticMatcher:
    """
    Hybrid semantic matching engine.
    Uses ID patterns, substring matching, and contextual co-occurrence.
    Stays deterministic where possible to compensate for Phi-3 Mini precision.
    """
    def __init__(self, co_occurrence_data: Dict[str, List[str]] = None):
        # co_occurrence_data: { chunk_id: [entity_name1, entity_name2, ...] }
        self.co_occurrence_map = co_occurrence_data or {}

    def score_match(self, entity_a: Dict, entity_b: Dict) -> float:
        """
        Computes a similarity score [0.0 - 1.0] between two entities.
        """
        score = 0.0
        
        id_a = str(entity_a.get("id", "")).upper()
        id_b = str(entity_b.get("id", "")).upper()
        name_a = str(entity_a.get("name", "")).lower()
        name_b = str(entity_b.get("name", "")).lower()
        chunk_a = entity_a.get("_chunk_id")
        chunk_b = entity_b.get("_chunk_id")

        # Priority 0: Same chunk boost (very strong contextual indicator)
        if chunk_a and chunk_b and chunk_a == chunk_b:
            score += 0.15

        # Priority 1: Direct ID match
        if id_a != "UNKNOWN" and id_a == id_b:
            score += 0.9
            
        # Priority 2: Variable/Parameter name reference in logic (Condition/Action)
        # If A is condition/action, find if B is referenced
        if (id_b in name_a or name_b in name_a) and id_b != "":
            score += 0.5
        elif (id_a in name_b or name_a in name_b) and id_a != "":
            score += 0.5
            
        # Priority 3: Equipment mention
        # If one is equipment and the other mentions it
        if "EQ" in id_a or "P-" in id_a or "V-" in id_a:
            if id_a in name_b or name_a in name_b:
                score += 0.4

        # Priority 4: Semantic / Jaccard
        words_a = set(re.findall(r'\w+', name_a))
        words_b = set(re.findall(r'\w+', name_b))
        if words_a and words_b:
            jaccard = len(words_a & words_b) / len(words_a | words_b)
            score += jaccard * 0.2
        
        return min(score, 1.0)

    def find_best_matches(self, target_entity: Dict, candidates: List[Dict], threshold: float = 0.4) -> List[Dict]:
        matches = []
        for cand in candidates:
            score = self.score_match(target_entity, cand)
            if score >= threshold:
                cand_copy = cand.copy()
                cand_copy["match_score"] = score
                matches.append(cand_copy)
        
        # Sort by score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
