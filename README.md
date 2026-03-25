# ⏻ ORION | Control Narrative Intelligence

ORION is a high-performance, local-first agentic AI platform designed to transform industrial **Control Narrative** documents into structured engineering insights. It leverages a sophisticated multi-agent pipeline to extract technical entities, map complex control logic, and generate deterministic **IEC 61131-3 Structured Text (ST)**.

---

## 🛠️ Technology Stack

### **Backend (The Engine)**
- **Framework:** Flask (Python 3.9+)
- **AI Orchestration:** Pure Sequential Semantic Pipeline (Custom Architecture)
- **Local LLM Hosting:** [Ollama](https://ollama.com/)
- **PDF Processing:** `pdfminer.six` (Semantic extraction) & `split_pdf` (Page isolation)

### **Frontend (Refined Industrial UI)**
- **Styling:** Custom Vanilla CSS3 (Glassmorphism, Neon-Industrial Aesthetic)
- **Typography:** `DM Sans` (Geometric Sans-Serif) & `Fira Code` (Monospaced Logic)
- **Animations:** CSS-only keyframe sequences for non-blocking UI performance.

### **AI Models**
- **Primary Model:** `qwen2.5:14b` (High-precision reasoning for technical extraction)
- **Fallback Model:** `llama3.1:8b` (Lightweight fallback for resilient processing)

---

## 🧠 The Agentic AI Pipeline (5-Phase Sequential)

Unlike traditional RAG or parallel extraction methods, ORION uses a **strictly sequential semantic chain** to maintain deep context and prevent data loss across document boundaries.

### **1. Document Structure Agent**
- **Role:** Semantically segments the document into logical 'Equipment Contexts'.
- **Logic:** Identifies where one PID loop ends and another begins based on semantic headers rather than fixed regex patterns.

### **2. Semantic Entity Extraction Agent**
- **Role:** Extracts core technical tokens: **Equipment, Variables, Parameters, Conditions, and Actions**.
- **Logic:** USes zero-shot prompting to identify entities in situ, ensuring that every condition is tied to its specific technical variable.

### **3. Control Logic Extraction Agent**
- **Role:** Maps the relationship between conditions and actions.
- **Logic:** Deduces the causal "Rules" that drive the control behavior (e.g., *IF X THEN Y*).

### **4. Semantic Logic Synthesis Agent**
- **Role:** Correlates extracted entities with logic rules into a unified tabular structure.
- **Logic:** Resolves naming inconsistencies and ensures cross-referential integrity between different document sections.

### **5. Pseudocode Generation Agent**
- **Role:** Generates human-readable PLC logic and IEC 61131-3 Structured Text.
- **Logic:** Converts textual logic into symbolic math expressions (e.g., `PV > HighLimit`) for deterministic industrial execution.

---

## 🧵 Concurrency & Threading Model

ORION balances server responsiveness with processing intensity through a hybrid threading strategy:

1.  **Background Document Processing:** When a file is uploaded, `app.py` spawns a dedicated `threading.Thread` to handle the heavy AI pipeline. This allows the Flask server to remain responsive, returning a `job_id` immediately so the frontend can poll for progress.
2.  **Sequential AI Execution:** Inside the background thread, the LLM calls are executed **sequentially**. This is a deliberate design choice: parallel LLM calls for a single document often lead to "context drift" and duplication. By moving sequentially, each agent builds upon the verified output of the previous one.

---

## 🚀 The 4-Stage Industrial Journey

The end-to-end processing flow is visualized as a 4-node journey on the ORION dashboard:

| Stage | Activity | Output |
| :--- | :--- | :--- |
| **Stage 1** | **Ingestion** | Document segmentation and text-layer preparation. |
| **Stage 2** | **Extraction** | 5-category entity discovery via Semantic Agents. |
| **Stage 3** | **Synthesis** | Unified Control Table generation and logic correlation. |
| **Stage 4** | **Generation** | Final PLC Pseudocode and Structured Text export. |

---

## 🛡️ Identity & Security
- **Local Processing:** All AI reasoning is performed on-device via Ollama. No document data leaves your local environment.
- **Deterministic Guardrails:** The final ST code is verified by a deterministic Python parser to ensure logical consistency before display.

Produced by **Vidyadhar Pothula** | *Standardizing Engineering Intelligence.*
