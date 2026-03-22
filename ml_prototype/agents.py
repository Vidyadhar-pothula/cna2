import json
from typing import Dict, List, Any

def robust_json_parse(text: str) -> Dict[str, Any]:
    """Helper to extract JSON from LLM outputs cleanly."""
    try:
        if "```json" in text:
            text = text.split("```json")[-1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[-1].split("```")[0]
        
        # Sometimes models wrap in text or leave trailing commas
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]  # type: ignore
            return json.loads(json_str)
        return {}
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {e}")

class SemanticAgentBase:
    def __init__(self, primary_llm, fallback_llm):
        self.primary_llm = primary_llm
        self.fallback_llm = fallback_llm

    def _invoke_with_fallback(self, prompt: str, schema_check=None) -> Dict[str, Any]:
        """
        Invokes the primary model. If it fails, times out, or returns an invalid schema,
        it falls back to the secondary model.
        """
        import time
        from langchain_core.runnables.config import RunnableConfig  # type: ignore # pylint: disable=import-error
        
        # We manually emulate a timeout since standard invoke might hang
        # Langchain provides timeout configs
        config = RunnableConfig(metadata={"timeout": 60}) # 60s timeout for large reasoning
        
        error_msg = ""
        try:
            # 1. Primary Model (qwen2.5:14b)
            response = self.primary_llm.invoke(prompt, config=config)
            result = robust_json_parse(response)
            if schema_check:
                schema_check(result)
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"[AGENT] Primary model failed ({e}). Falling back to llama3.1:8b...")
        
        # 2. Fallback Model (llama3.1:8b)
        try:
            response = self.fallback_llm.invoke(prompt, config=config)
            result = robust_json_parse(response)
            if schema_check:
                schema_check(result)
            return result
        except Exception as e:
            print(f"[AGENT] Fallback model also failed: {e}")
            raise RuntimeError(f"Both models failed. Primary Error: {error_msg}. Fallback Error: {e}")


class DocumentStructureAgent(SemanticAgentBase):
    """
    AGENT 1
    Purpose: semantically segment the document.
    """
    def segment(self, full_text: str) -> Dict[str, Any]:
        prompt = f"""
        ACT AS: Expert Industrial Systems Architect.
        TASK: Semantically analyze the following control narrative and segment it into logical equipment sections.
        Do NOT use regex. Rely entirely on your understanding of the engineering context, looking for natural section boundaries (e.g., "2.2 Surge Vessel", "2.2.1 Addition Control").
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "sections": [
                {{
                    "section_title": "Title of the section",
                    "equipment_context": "The primary equipment discussed in this section",
                    "content": "The exact verbatim text of this section"
                }}
            ]
        }}
        
        NARRATIVE TEXT:
        {full_text}
        
        Return ONLY valid JSON.
        """
        
        def validate(data):
            if "sections" not in data or not isinstance(data["sections"], list):
                raise ValueError("Missing 'sections' array.")
            if len(data["sections"]) > 0 and "content" not in data["sections"][0]:
                raise ValueError("Sections missing 'content' field.")
                
        return self._invoke_with_fallback(prompt, schema_check=validate)


class SemanticEntityExtractionAgent(SemanticAgentBase):
    """
    AGENT 2
    Purpose: semantically extract Equipment, Variables, Parameters, Conditions, and Actions.
    """
    def extract_entities(self, section_text: str, equipment_context: str) -> Dict[str, List[Dict]]:
        prompt = f"""
        ACT AS: Expert Control Systems Engineer.
        TASK: Extract all entities (Equipment, Variables, Parameters, Conditions, Actions) from the section.
        CONTEXT: The primary equipment focus is "{equipment_context}".
        
        RULES:
        1. Extract purely based on semantic meaning, not patterns.
        2. If an ID exists in text (e.g., 'SV01'), use it. If no ID exists, generate a precise one (e.g., 'EQP-SURGE-01').
        3. Do NOT summarize; preserve exact descriptions.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "equipment": [{{"id": "...", "name": "...", "description": "..."}}],
            "variables": [{{"id": "...", "name": "...", "description": "..."}}],
            "parameters": [{{"id": "...", "name": "...", "description": "..."}}],
            "conditions": [{{"id": "...", "name": "...", "description": "..."}}],
            "actions": [{{"id": "...", "name": "...", "description": "..."}}]
        }}
        
        TEXT:
        {section_text}
        
        Return ONLY valid JSON.
        """
        
        def validate(data):
            for key in ["equipment", "variables", "parameters", "conditions", "actions"]:
                if key not in data:
                    raise ValueError(f"Missing '{key}' array.")
                    
        return self._invoke_with_fallback(prompt, schema_check=validate)


class ControlLogicExtractionAgent(SemanticAgentBase):
    """
    AGENT 3
    Purpose: semantically interpret cause-effect logic between conditions and actions.
    """
    def extract_logic(self, section_text: str) -> List[Dict[str, str]]:
        prompt = f"""
        ACT AS: Automation Logic Designer.
        TASK: Semantically interpret the text to identify cause-effect relationships.
        Extract the underlying logical rules mapping conditions to actions for specific equipment.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "rules": [
                {{
                    "equipment": "Name of the module/equipment",
                    "condition": "Logical condition (e.g., pH < Setpoint AND HiSideEnabled)",
                    "action": "Consequent action (e.g., AddBase)"
                }}
            ]
        }}
        
        TEXT:
        {section_text}
        
        Return ONLY valid JSON.
        """
        
        def validate(data):
            if "rules" not in data:
                raise ValueError("Missing 'rules' array in logic extraction.")
                
        result = self._invoke_with_fallback(prompt, schema_check=validate)
        return result.get("rules", [])


class SemanticLogicSynthesisAgent(SemanticAgentBase):
    """
    AGENT 4
    Purpose: Combine entities and logic rules into a unified control table.
    """
    def synthesize(self, entities: Dict, logic_rules: List[Dict]) -> List[Dict]:
        # We pass the extracted JSON objects back to the LLM to do semantic joining
        prompt = f"""
        ACT AS: Senior Systems Integrator.
        TASK: Combine the extracted Entities and Logic Rules into a consolidated, unified control table.
        
        RULES:
        1. Ensure conditions are correctly mapped to their respective equipment.
        2. Ensure referenced variables and parameters exist in the context.
        3. Output an array representing rows of the unified table.
        
        INPUT ENTITIES: {json.dumps(entities)}
        INPUT LOGIC: {json.dumps(logic_rules)}
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "unified_table": [
                {{
                    "equipment": "Equipment Name",
                    "variables": "Variable Names",
                    "parameters": "Parameter Names",
                    "condition": "Target Condition",
                    "action": "Target Action"
                }}
            ]
        }}
        
        Return ONLY valid JSON.
        """
        
        def validate(data):
            if "unified_table" not in data:
                raise ValueError("Missing 'unified_table' array.")
                
        result = self._invoke_with_fallback(prompt, schema_check=validate)
        return result.get("unified_table", [])


class PseudocodeGenerationAgent(SemanticAgentBase):
    """
    AGENT 5
    Purpose: Generate equipment-specific pseudocode derived straight from the unified table.
    """
    def generate_code(self, unified_table: List[Dict]) -> str:
        prompt = f"""
        ACT AS: PLC Programmer.
        TASK: Generate equipment-specific pseudocode derived STRICTLY from the unified control table provided.
        Each equipment must receive its own distinct pseudocode block. Use structured logic (READ, IF, THEN, ENDIF).
        
        EXAMPLE FORMAT:
        SV01 – Surge Vessel
        READ VesselWeight
        IF VesselWeight > HighWeightLimit THEN
            DisableAdditionControl
        ENDIF
        
        UNIFIED TABLE:
        {json.dumps(unified_table, indent=2)}
        
        Return ONLY the raw pseudocode text (NO markdown formatting or conversational filler).
        """
        
        try:
            # We use a direct invoke because the output is text, not strict JSON
            response = self.primary_llm.invoke(prompt)
            return response.replace("```pseudocode", "").replace("``` text", "").replace("```", "").strip()
        except Exception:
            response = self.fallback_llm.invoke(prompt)
            return response.replace("```pseudocode", "").replace("``` text", "").replace("```", "").strip()
