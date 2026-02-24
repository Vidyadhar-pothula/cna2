from typing import List, Dict
from ml_prototype.semantic_matcher import SemanticMatcher

class UnifiedStitcher:
    """
    Constructs the final Unified Control Table by stitching entities together.
    Uses clustering based on semantic proximity to Equipment nodes.
    """
    def __init__(self, matcher: SemanticMatcher):
        self.matcher = matcher

    def stitch(self, normalized_data: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Input: Normalized dictionary of entities by category.
        Output: List of rows for the Unified Control Table.
        """
        equipment_list = normalized_data.get("equipment", [])
        variables = normalized_data.get("variables", [])
        parameters = normalized_data.get("parameters", [])
        conditions = normalized_data.get("conditions", [])
        actions = normalized_data.get("actions", [])

        unified_rows = []
        processed_entities = set() # To avoid duplicate rows for the same logic

        # Strategy: Iterate through logic nodes (Conditions/Actions) as they are the "core" of a control row
        logic_entities = conditions + actions
        
        for logic in logic_entities:
            logic_key = f"{logic.get('id')}_{logic.get('name')}"
            if logic_key in processed_entities: continue
            
            # Find related entities for this logic node
            rel_equip = self.matcher.find_best_matches(logic, equipment_list, threshold=0.45)
            rel_vars = self.matcher.find_best_matches(logic, variables, threshold=0.45)
            rel_params = self.matcher.find_best_matches(logic, parameters, threshold=0.45)
            
            # If this is a condition, find related actions in the same chunk
            if logic in conditions:
                rel_others = self.matcher.find_best_matches(logic, actions, threshold=0.45)
                cond_val = self._fmt(logic)
                act_val = ", ".join([self._fmt(a) for a in rel_others])
                for a in rel_others: processed_entities.add(f"{a.get('id')}_{a.get('name')}")
            else: # It's an action
                rel_others = self.matcher.find_best_matches(logic, conditions, threshold=0.45)
                act_val = self._fmt(logic)
                cond_val = ", ".join([self._fmt(c) for c in rel_others])
                for c in rel_others: processed_entities.add(f"{c.get('id')}_{c.get('name')}")

            row = {
                "equipment": ", ".join([self._fmt(e) for e in rel_equip]) or "Global System",
                "variable": ", ".join([self._fmt(v) for v in rel_vars]),
                "parameter": ", ".join([self._fmt(p) for p in rel_params]),
                "condition": cond_val,
                "action": act_val
            }
            unified_rows.append(row)
            processed_entities.add(logic_key)

        # Add leftover equipment that has no associated logic
        for equip in equipment_list:
            if not any(equip['id'] in row['equipment'] for row in unified_rows):
                unified_rows.append({
                    "equipment": self._fmt(equip),
                    "variable": "", "parameter": "", "condition": "", "action": ""
                })

        return unified_rows

    def _fmt(self, item: Dict) -> str:
        name = item.get('name', '')
        id_val = item.get('id', '')
        if id_val and id_val != "UNKNOWN":
            return f"{name} ({id_val})"
        return name

    def _get_name_at(self, entity_list: List[Dict], index: int) -> str:
        if index < len(entity_list):
            item = entity_list[index]
            return f"{item['name']} ({item['id']})" if item.get('id') != "UNKNOWN" else item['name']
        return ""
