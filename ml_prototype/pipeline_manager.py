import os
import json
from typing import Dict, List
from ml_prototype.global_context_builder import GlobalContextBuilder
from ml_prototype.extraction_agents import ParallelExtractionOrchestrator
from ml_prototype.normalization_engine import NormalizationEngine
from ml_prototype.semantic_matcher import SemanticMatcher
from ml_prototype.unified_stitcher import UnifiedStitcher

class PipelineManager:
    """
    Orchestrates the Scalable Agentic Pipeline.
    """
    def __init__(self, llm):
        self.llm = llm
        self.context_builder = GlobalContextBuilder(llm)
        self.extractor = ParallelExtractionOrchestrator(llm)
        self.normalizer = NormalizationEngine()
        self.matcher = SemanticMatcher()
        self.stitcher = UnifiedStitcher(self.matcher)

    def run_pipeline(self, full_text: str) -> Dict:
        import time
        start_total = time.time()
        
        print("--- PHASE 1: Global Context Building (Parallel) ---")
        t0 = time.time()
        self.context_builder.process_document(full_text)
        global_context = self.context_builder.get_summary()
        print(f"  -> Context Building took {time.time()-t0:.2f}s")
        
        # Split text for detailed extraction
        chunks = self.context_builder.chunk_text(full_text)
        
        print("--- PHASE 2: Parallel Extraction ---")
        t1 = time.time()
        raw_results = self.extractor.run_parallel(chunks, global_context)
        print(f"  -> Extraction took {time.time()-t1:.2f}s")
        
        print("--- PHASE 3: Normalization & Deduplication ---")
        t2 = time.time()
        normalized_data = self.normalizer.process_results(raw_results)
        print(f"  -> Normalization took {time.time()-t2:.2f}s")
        # 4. Final Stitching
        print("--- PHASE 4: Semantic Matching & Stitching ---")
        start_time = time.time()
        
        # Ensure regex fallback items are at least present in normalized_data
        # This handles cases where LLM found NOTHING but regex found items
        summary = self.context_builder.get_summary()
        if not normalized_data.get("equipment") and summary.get("equipment"):
            normalized_data["equipment"] = [{"id": e, "name": e, "description": "Discovered via Regex"} for e in summary["equipment"]]
        if not normalized_data.get("variables") and summary.get("variables"):
            normalized_data["variables"] = [{"id": v, "name": v, "description": "Discovered via Regex"} for v in summary["variables"]]

        unified_table = self.stitcher.stitch(normalized_data)
        stitching_time = time.time() - start_time
        print(f"  -> Stitching took {stitching_time:.2f}s")
        
        print("--- PHASE 5: Implementation Code Generation ---")
        t4 = time.time()
        pseudocode = self.generate_pseudocode(unified_table)
        print(f"  -> Code Gen took {time.time()-t4:.2f}s")
        
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
                "engine": "ScalableAgenticPipeline-v3 (Production)",
                "model": "phi3-mini-strict"
            }
        }

    def generate_pseudocode(self, unified_table: List[Dict]) -> str:
        """
        Generates professionally formatted Structured Text (ST) code.
        Uses a hybrid approach: LLM for logic conversion, Python for indentation.
        """
        if not unified_table:
            return "// No logic extracted."
            
        # 1. First, use LLM to refine narrative strings into symbolic-style expressions where needed
        # We process in batches to maintain context without overloading
        refined_rows = []
        for row in unified_table[:15]: # Limit to avoid token collapse
            refined_row = row.copy()
            if row.get("condition") or row.get("action"):
                prompt = f"Convert this narrative to short symbolic code (e.g. 'Level > High' instead of 'when level exceeds high limit').\nInput: {row['condition']} -> {row['action']}\nShort Code Format: COND: [Logic] | ACT: [Action]"
                try:
                    resp = self.llm.invoke(prompt).strip()
                    if "COND:" in resp and "ACT:" in resp:
                        parts = resp.split("|")
                        refined_row["condition"] = parts[0].replace("COND:", "").strip()
                        refined_row["action"] = parts[1].replace("ACT:", "").strip()
                except:
                    pass
            refined_rows.append(refined_row)

        # 2. Use Deterministic Formatter for the structural "Shell"
        return self._build_st_code(refined_rows)

    def _build_st_code(self, rows: List[Dict]) -> str:
        output = [
            "(* ****************************************************** *)",
            "(* ORION GENERATED CONTROL LOGIC (IEC 61131-3 ST)         *)",
            "(* ****************************************************** *)",
            ""
        ]
        
        for row in rows:
            equip = row.get("equipment", "Unknown")
            cond = row.get("condition", "").strip()
            act = row.get("action", "").strip()
            
            if not cond and not act:
                continue
                
            output.append(f"// Control Logic for: {equip}")
            if cond:
                output.append(f"IF {cond} THEN")
                if act:
                    output.append(f"    {act};")
                else:
                    output.append(f"    // No explicit action defined;")
                output.append("END_IF;")
            elif act:
                output.append(f"{act}; // Unconditional execution")
            output.append("") # Spacer
            
        return "\n".join(output)
