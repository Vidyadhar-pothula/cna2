# ⏻ ORION | Control Narrative Intelligence

ORION is a specialized platform that reads industrial **Control Narrative** PDFs and automatically turns them into structured data and ready-to-use **PLC Code** (Structured Text).

---

## 🛠️ The Tech Stack
- **Backend:** Python Flask
- **AI Brain:** Local Ollama (running the **Qwen 2.5 14B** model)
- **Frontend:** Modern "Refined Industrial" UI using **DM Sans** typography
- **Privacy:** Every analysis happens 100% locally on your machine.

---

## ⚙️ How it Works: The 5 Processing Stages

ORION processes your documents in five clear, simple stages:

### **Stage 1: PDF Ingestion & Reading**
The system first "reads" the PDF, extracting every character and identifying the major sections (like "Tank Control" or "Emergency Shutdown"). 

### **Stage 2: 3-Agent Parallel Extraction**
To ensure speed and accuracy, ORION launches **3 Parallel Agentic AI Workers**. These agents scan the text simultaneously to find raw information:
- **Agent A:** Looks for physical Equipment.
- **Agent B:** Identifies Process Variables and Setpoints (Parameters).
- **Agent C:** Detects specific Conditions and required Actions.

### **Stage 3: The 5-Table Generation**
The raw data from the agents is cleaned up and organized into **5 Structured Research Tables**:
1. **Equipment Table** (List of all hardware found)
2. **Variables Table** (List of all live sensors/signals)
3. **Parameters Table** (List of all setpoints/thresholds)
4. **Conditions Table** (Specific logic states identified)
5. **Actions Table** (Specific commands to be sent)

### **Stage 4: Single Table Unification (The Logic Map)**
The system then "stitches" all 5 tables together into a single **Unified Control Table**. This maps precisely which *Condition* on a specific *Variable* triggers which *Action* for a specific piece of *Equipment*.

### **Stage 5: Final Pseudocode & Code Generation**
Finally, the "Integrator" role takes the Unified Table and writes **IEC 61131-3 Structured Text**. This is the actual code used in industrial PLCs to run the plant logic.

---

## 👥 Core AI Roles

Instead of complex AI names, think of ORION as a team of 3 specialists:
1. **The Reader:** Handles Stage 1 (Getting the text ready).
2. **The Specialist Finder:** Handles Stage 2 & 3 (Running parallel searches for the 5 data types).
3. **The Logic Builder:** Handles Stage 4 & 5 (Connecting the dots and writing the final code).

---

Produced by **Vidyadhar Pothula** | *Standardizing Engineering Intelligence.*
