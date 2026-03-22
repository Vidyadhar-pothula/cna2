# Control Narrative Analysis (ORION Server)

Welcome to the **Control Narrative Analysis** (ORION) project. This repository hosts a scalable, agentic AI pipeline designed to ingest industrial control narrative PDFs and automatically extract highly structured control logic (Equipment, Variables, Parameters, Conditions, Actions) and generate industry-standard **IEC 61131-3 Structured Text (ST)** code.

## 🧠 AI Models & Agents Used

The system employs a hybrid, multi-agent architecture to maximize accuracy and reliability for complex engineering documents.

### 1. Primary AI (Local / Scalable)
- **Model:** `phi3:mini` (managed via Ollama, configurable via `EXTRACTION_MODEL`).
- **Role:** Handles the heavy lifting of pure text-based reasoning and logic extraction. Runs locally for privacy and cost-efficiency.

### 2. Vision / Fallback AI (Cloud)
- **Model:** `gemini-2.0-flash` (via Google Gemini API).
- **Role:** Acts as the **Vision Fallback Agent**. If the system detects a scanned PDF (i.e., text extraction yields almost no characters), it automatically reroutes the document to Gemini's multimodal File API to perform visual OCR and entity extraction simultaneously.

### 3. Spatial Extractor (Optional ML)
- **Model:** `LayoutLMv3` (HuggingFace).
- **Role:** Used for understanding complex structural layouts and bounding boxes in PDFs, aligning visual structures with text (when enabled).

---

## ⚙️ The Agentic Pipeline (Internal Flow)

When a document is uploaded, it is routed through the **Scalable Agentic Pipeline** (`PipelineManager`). Let's break down the 5 distinct phases of the internal flow:

### Phase 1: Global Context Building 
- **Agent:** `GlobalContextBuilder`
- The entire raw text is ingested, and a **Summarization Agent** scans the document.
- **Regex Augmentation:** It relies on strict regular expressions to reliably identify standard tag formats (e.g., `PT-101`) to ensure zero hallucinations for critical equipment IDs. The text is then chunked for parallel processing.

### Phase 2: Parallel Extraction Orchestration
- **Agent:** `ParallelExtractionOrchestrator` -> spawns multiple `ExtractionAgent` instances.
- **Flow:** The system spins up a thread pool (max 4 workers). Each chunk of text is analyzed simultaneously by an LLM agent prompted with a strict "Industrial Controls Engineer" persona.
- **Action:** The agents extract 5 core categories simultaneously using a 1-shot prompted JSON schema:
  1. Equipment
  2. Variables
  3. Parameters
  4. Conditions
  5. Actions

### Phase 3: Normalization & Deduplication
- **Engine:** `NormalizationEngine`
- Because the extraction happens in parallel chunks, there may be overlaps or formatting quirks. This engine rigorously cleans up the JSON, enforces strict schemas, parses out missing IDs, and removes duplicate entities.

### Phase 4: Semantic Matching & Stitching
- **Engine:** `SemanticMatcher` & `UnifiedStitcher`
- **Flow:** Takes the isolated arrays of conditions, actions, and equipment, and "stitches" them back together into a coherent logical table (`unified_control_table`). 
- **Hybrid Guardrail:** It cross-references the LLM's output with the exact Regex matches from Phase 1. If the LLM failed to identify an equipment tag that Regex found, the system defensively injects the Regex tag back into the dataset to prevent data loss.

### Phase 5: Implementation Code Generation
- **Flow:** Converts the parsed logic into actual industrial code.
- **Step A (LLM Logic Refinement):** The LLM is invoked again to compress human narrative strings (e.g., "when the pressure gets too high") into symbolic math expressions (e.g., `PT-101 > HighLimit`).
- **Step B (Deterministic Formatting):** A pure Python deterministic parser takes these exact symbols and formats them strictly into **IEC 61131-3 Structured Text** so that it compiles perfectly in modern PLCs.

---

## 🚀 System Architectural Stages

To give a holistic view, the entire project happens across these distinct **Stages**:

### **Stage 1: Ingestion & Preprocessing**
- **Upload:** The PDF document is received via the Flask backend (`app.py`).
- **Separation:** The `split_pdf.py` utility physically isolates text pages from image-heavy pages, creating two separate processing streams.

### **Stage 2: Intelligent Routing (Triage)**
- **Text Density Evaluation:** `tinyllama_service.py` checks exactly how many characters were extractable.
- **Decision Matrix:**
  - If text is rich -> **Route to Local Scalable AI** (`phi3:mini`).
  - If text is almost zero (<10 chars) -> flagged as a scanned image -> **Route to Vision AI** (`gemini-2.0-flash` File API OCR).

### **Stage 3: The Multi-Agent Extraction Pipeline**
This is the core execution logic (handled by `PipelineManager.run_pipeline()`), which itself carries 4 sub-stages:
1. **Context Building:** Scanning the global document and chunking into sections.
2. **Parallel Extraction:** Generating thread pools of LLM agents acting simultaneously on the chunks to find Entities (Equipment, Actions, etc).
3. **Normalization:** Cleaning and deduplicating data across agents into strict schemas.
4. **Stitching:** Rebuilding logical conditions and actions into uniform tables, injecting Regex fallback safety nets.

### **Stage 4: Post-Processing & Code Generation**
- **Logic Refinement:** The LLMs convert human narratives ("When High") into strict symbols (`> HighLimit`).
- **Structured Text Generator:** A deterministic Python parser reads the symbols and converts them exactly into IEC 61131-3 syntax.

### **Stage 5: Delivery & UI Rendering**
- **JSON Aggregation:** All tables and ST code are merged into a single structured schema payload.
- **Asynchronous Delivery:** An asynchronous worker thread completes the job and flags the REST API.
- **Frontend Hydration:** The HTML/JS client pulls the finalized payload and renders the interactive tables and code editor natively inside the browser (via `script.js` and `index.html`).
