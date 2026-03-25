# ⏻ ORION | Control Narrative Intelligence
*System Architecture & Workflow Documentation*

ORION is a specialized AI platform designed to transform industrial **Control Narrative** PDFs into structured engineering data and **IEC 61131-3 Structured Text**. This document outlines the technical architecture for use in system diagramming.

---

## 🏗️ Technical Architecture (Local-First Design)

ORION is built as an entirely self-contained, air-gapped system. All AI reasoning is performed on local hardware to ensure zero data egress and high-fidelity technical processing.

### **1. The Tech Stack**
- **Inference Engine:** [Ollama](https://ollama.com/) (Local server)
- **Primary AI Model:** **Qwen 2.5 14B** (Optimized for logical reasoning and industrial syntax)
- **Fallback AI Model:** **Llama 3.1 8B** (For redundant verification)
- **Backend Infrastructure:** Python 3.9+ (Flask) and **LangChain** (for agentic orchestration)
- **Front-end Design:** "Refined Industrial" system using **DM Sans** and a geometric glassmorphism aesthetic.

---

## ⚙️ The 5-Stage Sequential Pipeline

The document journey follows a **Strictly Sequential Semantic Chain**. This ensures that context builds cumulatively, preventing the data loss common in parallel processing.

### **Stage 1: Document Ingestion (The Architect Role)**
- **Action:** Raw PDF text is ingested and passed to the `DocumentStructureAgent`.
- **Purpose:** Segment the document into logical "Equipment Contexts" (e.g., Boiler, Tank, Pump Station).
- **Architecture Node:** `Segmentation & Boundary Mapping`.

### **Stage 2: Semantic Token Extraction (The Specialist Role)**
- **Action:** A sequential scan is performed on every identified segment.
- **Goal:** Identify **5 Key Technical Tokens**:
  - **Equipment:** Physical hardware units.
  - **Variables:** Live PV/Signal IDs.
  - **Parameters:** SPs and Deadbands.
  - **Conditions:** Operational triggers.
  - **Actions:** Control responses.
- **Architecture Node:** `Semantic Multi-Agent Extraction`.

### **Stage 3: 5-Table Synchronization & Normalization**
- **Action:** Raw tokens are semantically normalized by the `NormalizationEngine`.
- **Purpose:** Resolve naming conflicts (e.g., "Pump-1" vs "P1") and ensure one-to-one mapping across the entire document.
- **Architecture Node:** `Knowledge Graph Alignment`.

### **Stage 4: Unified Control Table Synthesis**
- **Action:** The `SemanticLogicSynthesisAgent` correlates Stage 2 tokens into a single **Unified Logic Map**.
- **Purpose:** Directly map `CONDITION` + `VARIABLE` $\rightarrow$ `ACTION` within a specific `EQUIPMENT` context.
- **Architecture Node:** `Logic Correlation & Mapping`.

### **Stage 5: Deterministic Code Generation (The Builder Role)**
- **Action:** The `PseudocodeGenerationAgent` converts the Logic Map into human-readable symbols and **IEC 61131-3 Structured Text**.
- **Architecture Node:** `PLC Code Synthesis (ST Generator)`.

---

## 💬 Secondary Intelligence Layer: ORION AI (Ask AI)

A dedicated context-aware chatbot integrated into the UI sidebar.
- **Engine:** Qwen 2.5 14B.
- **Capability:** Injects the current document's 5 Extraction Tables directly into the chat context. 
- **Usage:** Engineers can query specific interlocks, setpoints, or summaries directly from the sidebar.

---

## 👥 Core System Personas
For simplified architectural visualization:
1. **The Reader:** Manages Stage 1 (PDF boundary mapping).
2. **The Specialist Finder:** Manages Stage 2 & 3 (Detailed data discovery).
3. **The Logic Builder:** Manages Stage 4 & 5 (Integration and code export).

---

Produced by **Vidyadhar Pothula** | *Standardizing Engineering Intelligence.*
