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

## 🧠 The Agentic AI Pipeline (3 Core Semantic Roles)

Unlike traditional parallel extractors, ORION uses a **strictly sequential semantic chain** where 3 distinct "AI Roles" work in harmony to maintain deep technical context.

### **1. The Architect (Structure & Segmentation)**
- **Agent:** `DocumentStructureAgent`
- **Role:** Semantically segments the raw document into logical 'Equipment Contexts'.
- **Logic:** Identifies where one PID loop ends and another begins based on semantic headers rather than fixed regex patterns, defining the global context for the following agents.

### **2. The Extraction Specialist (Entities & Logic)**
- **Agents:** `SemanticEntityExtractionAgent` & `ControlLogicExtractionAgent`
- **Role:** Extracts technical tokens (Equipment, Variables, Conditions, Actions) and maps their causal relationships.
- **Logic:** This specialist performs a dual-pass extraction on each section identified by the Architect, ensuring that every control rule is tied to a verified technical variable found in situ.

### **3. The Systems Integrator (Synthesis & Generation)**
- **Agents:** `SemanticLogicSynthesisAgent` & `PseudocodeGenerationAgent`
- **Role:** Correlates extracted data into a unified logic table and generates the final code.
- **Logic:** Resolves naming inconsistencies, performs semantic cross-checks, and converts text-based logic into symbolic math expressions and **IEC 61131-3 Structured Text**.

---

## 🧵 Concurrency & Threading Model

ORION balances server responsiveness with processing intensity through a hybrid threading strategy:

1.  **Background Document Processing:** When a file is uploaded, `app.py` spawns a dedicated `threading.Thread` to handle the heavy AI pipeline. This allows the Flask server to remain responsive, returning a `job_id` immediately so the frontend can poll for progress.
2.  **Sequential AI Execution:** Inside the background thread, the LLM calls are executed **sequentially**. This is a deliberate design choice: parallel LLM calls for a single document often lead to "context drift" and duplication. By moving sequentially, each agent builds upon the verified output of the previous one.

---

## 🚀 The 3-Stage Industrial Journey

The end-to-end processing flow is visualized as a 3-node journey on the ORION dashboard, mapping directly to our core AI roles:

| Stage | Role | Output |
| :--- | :--- | :--- |
| **Stage 1** | **The Architect** | Document segmentation and equipment context mapping. |
| **Stage 2** | **The Specialist** | Semantic extraction of Entities (Eqp/Var) and Logic Rules. |
| **Stage 3** | **The Integrator** | Unified Control Table synthesis and IEC 61131-3 code export. |

---

## 🛡️ Identity & Security
- **Local Processing:** All AI reasoning is performed on-device via Ollama. No document data leaves your local environment.
- **Deterministic Guardrails:** The final ST code is verified by a deterministic Python parser to ensure logical consistency before display.

Produced by **Vidyadhar Pothula** | *Standardizing Engineering Intelligence.*
