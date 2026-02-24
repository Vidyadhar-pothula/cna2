import json
import os
import re
import concurrent.futures
from typing import List, Dict, Set

class GlobalContextBuilder:
    def __init__(self, llm, chunk_size=3000, overlap=500):
        self.llm = llm
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.global_registry = {
            "equipment": set(),
            "variables": set(),
            "parameters": set(),
            "sections": []
        }
        self.patterns = set()

    def chunk_text(self, text: str) -> List[str]:
        chunks = []
        if not text:
            return chunks
        
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            if end == len(text):
                break
            start += self.chunk_size - self.overlap
        return chunks

    def extract_local_entities(self, chunk: str) -> Dict:
        """
        Fast regex-based discovery to avoid LLM latency in Phase 1.
        """
        # Patterns for: Equipment (e.g. P-101, T-501, VT-201, Pump101, VLV-55)
        # Improved pattern: Matches Letter-Number, LetterNumber, and common industrial labels
        tag_pattern = r'\b(?:[A-Z]{1,4}[-_\s]?\d{1,6}[A-Z]{0,2})\b|\b(?:VLV|PMP|TNK|HE|COMP|GEN|MTR)-?\d{1,4}\b'
        tags = set(re.findall(tag_pattern, chunk))
        
        # Patterns for: Variables (Common Engineering Keywords)
        var_keywords = [
            "Level", "Pressure", "Temperature", "Flow", "Vibration", "Speed", 
            "Position", "Speed", "Frequency", "Current", "Voltage", "Power",
            "State", "Status", "Command", "Feedback", "Alarm", "Trip", "Limit"
        ]
        vars_found = set()
        for kw in var_keywords:
            if re.search(fr'\b{kw}\b', chunk, re.I):
                vars_found.add(kw)
        
        # Pattern for: Potential Setpoints/Parameters
        param_pattern = r'\b\d+(?:\.\d+)?\s?(?:%|Hz|bar|m|kg|s|rpm|degC|V|A|kW)\b'
        params = set(re.findall(param_pattern, chunk))

        return {
            "equipment": list(tags),
            "variables": list(vars_found),
            "parameters": list(params),
            "section": None
        }

    def process_document(self, text: str):
        chunks = self.chunk_text(text)
        print(f"GlobalContextBuilder: Processing {len(chunks)} chunks in parallel...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_chunk = {executor.submit(self.extract_local_entities, chunk): chunk for chunk in chunks}
            for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk)):
                try:
                    entities = future.result()
                    self.global_registry["equipment"].update(entities.get("equipment", []))
                    self.global_registry["variables"].update(entities.get("variables", []))
                    self.global_registry["parameters"].update(entities.get("parameters", []))
                    if entities.get("section"):
                        self.global_registry["sections"].append(entities["section"])
                    print(f"  Processed {i+1}/{len(chunks)} context chunks...")
                except Exception as e:
                    print(f"Error processing context chunk: {e}")

    def get_summary(self) -> Dict:
        return {
            "equipment": list(self.global_registry["equipment"]),
            "variables": list(self.global_registry["variables"]),
            "parameters": list(self.global_registry["parameters"]),
            "sections": list(set(self.global_registry["sections"])) # Deduplicate sections
        }

    def save_context(self, path: str):
        summary = self.get_summary()
        with open(path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Global context saved to {path}")
