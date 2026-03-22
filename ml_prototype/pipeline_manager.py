import time
from typing import Dict, Any

from .agents import (  # type: ignore # noqa: E402 # pylint: disable=import-error
    DocumentStructureAgent,
    SemanticEntityExtractionAgent,
    ControlLogicExtractionAgent,
    SemanticLogicSynthesisAgent,
    PseudocodeGenerationAgent
)
from .normalization_engine import SemanticNormalizationEngine  # type: ignore # noqa: E402 # pylint: disable=import-error

class PipelineManager:
    """
    Orchestrates the purely Sequential Semantic Agentic Pipeline.
    NO Parallel Extraction. NO Regex matching.
    """
    def __init__(self, primary_llm, fallback_llm):
        self.primary_llm = primary_llm
        self.fallback_llm = fallback_llm
        
        # Initialize the 5 core agents
        self.structure_agent = DocumentStructureAgent(primary_llm, fallback_llm)
        self.extraction_agent = SemanticEntityExtractionAgent(primary_llm, fallback_llm)
        self.logic_agent = ControlLogicExtractionAgent(primary_llm, fallback_llm)
        self.synthesis_agent = SemanticLogicSynthesisAgent(primary_llm, fallback_llm)
        self.pseudocode_agent = PseudocodeGenerationAgent(primary_llm, fallback_llm)
        
        # Initialize semantic normalizer
        self.normalizer = SemanticNormalizationEngine(primary_llm, fallback_llm)

    def run_pipeline(self, full_text: str) -> Dict[str, Any]:
        print("=== STARTING SEMANTIC AGENTIC PIPELINE (SEQUENTIAL) ===")
        start_total = time.time()
        
        # --- AGENT 1: Document Structure ---
        print("[AGENT 1] Structuring Document Semantically...")
        t0 = time.time()
        structure_obj = self.structure_agent.segment(full_text)
        sections = structure_obj.get("sections", [])
        print(f"  -> Generated {len(sections)} semantic sections in {time.time()-t0:.2f}s")
        
        # Accumulators
        raw_entities = {
            "equipment": [], "variables": [], "parameters": [], "conditions": [], "actions": []
        }
        raw_logic_rules = []

        # --- AGENT 2 & 3: Sequential Entity & Logic Extraction per Section ---
        print("[AGENT 2 & 3] Extracting Entities and Logic sequentially per section...")
        t1 = time.time()
        for idx, sec in enumerate(sections):
            print(f"  -> Processing Section {idx+1}/{len(sections)}: {sec.get('section_title', 'Unknown')}")
            content = sec.get("content", "")
            context = sec.get("equipment_context", "Unknown Equipment")
            
            # Agent 2: Fetch Entities
            extracted_entities = self.extraction_agent.extract_entities(content, context)
            for k in raw_entities.keys():
                raw_entities[k].extend(extracted_entities.get(k, []))
            
            # Agent 3: Fetch Logic Rules
            logic_rules = self.logic_agent.extract_logic(content)
            raw_logic_rules.extend(logic_rules)
            
        print(f"  -> Sequential Extraction took {time.time()-t1:.2f}s")
        
        # --- NORMALIZATION ---
        print("[NORMALIZATION] Semantically normalizing extracted entities...")
        t_norm = time.time()
        normalized_data = self.normalizer.normalize(raw_entities)
        print(f"  -> Normalization took {time.time()-t_norm:.2f}s")
        
        # --- AGENT 4: Semantic Logic Synthesis ---
        print("[AGENT 4] Synthesizing control logic table semantically...")
        t_synth = time.time()
        unified_table = self.synthesis_agent.synthesize(normalized_data, raw_logic_rules)
        print(f"  -> Synthesis took {time.time()-t_synth:.2f}s")
        
        # --- AGENT 5: Pseudocode Generation ---
        print("[AGENT 5] Generating equipment-specific pseudocode...")
        t_code = time.time()
        pseudocode = self.pseudocode_agent.generate_code(unified_table, normalized_data)
        print(f"  -> Pseudocode generation took {time.time()-t_code:.2f}s")

        total_time = time.time() - start_total
        print(f"=== TOTAL PIPELINE TIME: {total_time:.2f}s ===")
        
        return {
            "equipment_table": normalized_data.get("equipment", []),
            "variables_table": normalized_data.get("variables", []),
            "parameters_table": normalized_data.get("parameters", []),
            "conditions_table": normalized_data.get("conditions", []),
            "actions_table": normalized_data.get("actions", []),
            "unified_control_table": unified_table,
            "pseudocode": pseudocode,
            "metadata": {
                "engine": "Sequential Semantic Architecture v4",
                "primary_model": "qwen2.5:14b",
                "fallback_model": "llama3.1:8b"
            }
        }
