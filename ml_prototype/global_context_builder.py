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
        
        # Increase chunk size for small documents to ensure full context
        chunk_size = 10000
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            if end == len(text):
                break
            start += chunk_size - self.overlap
        return chunks

    def extract_local_entities(self, chunk: str) -> Dict:
        """
        Keyword-based semantic hints. Helps LLM focus on key areas.
        """
        # We use a set of common industrial keywords as 'semantic anchors'
        anchors = ["Pump", "Tank", "Valve", "Level", "Pressure", "Flow", "Temperature", "Open", "Close", "Stop", "Start"]
        found_anchors = [a for a in anchors if a.lower() in chunk.lower()]
        
        # We also look for potential Tags (Alpha-Numeric patterns) but treat them as generic hints
        tag_hints = re.findall(r'\b[A-Z]{1,4}[-_\d]{1,6}\b', chunk)

        return {
            "equipment": list(set(found_anchors + tag_hints)),
            "variables": [],
            "parameters": [],
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
