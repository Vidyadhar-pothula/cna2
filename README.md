# Control Narrative Analysis Pipeline

An agentic AI pipeline for extracting structured control logic from industrial PDF documents. This system utilizes a multi-agent orchestrated approach (via Ollama/Phi-3 or Gemini) to digitize, analyze, and normalize complex control narratives into structured datasets and pseudocode.

## 🚀 Features

- **Multi-Agent Orchestration**: Parallel agents for specialized entity extraction (Equipment, Variables, Parameters, Conditions, Actions).
- **Hybrid Extraction**: Combines LLM reasoning with reliable regex-based scan patterns.
- **Auto-Normalization**: Strict schema enforcement for extracted tables.
- **Logic Translation**: Generates Structured Text (ST) pseudocode from narrative descriptions.
- **PDF Processing**: Integrated PDF splitting and OCR-ready digitization.
- **Web Interface**: Clean, interactive UI for uploading narratives and visualizing the extraction flow.

## 🛠️ Tech Stack

- **Backend**: Python, Flask, LangChain, Ollama
- **Frontend**: HTML5, Vanilla CSS, Javascript
- **ML Models**: Phi-3 Mini (Local), Gemini (Fallback)
- **PDF Engine**: PyMuPDF (fitz), pdf2image

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Vidyadhar-pothula/control-narrative-analysis.git
   cd control-narrative-analysis
   ```

2. **Install dependencies**:
   ```bash
   pip install -r ml_prototype/requirements.txt
   ```

3. **Set up Environment**:
   Create a `.env` file with your `GEMINI_API_KEY` (optional for fallback).

4. **Ensure Ollama is running**:
   Make sure you have `ollama` installed and the `phi3:mini` model pulled:
   ```bash
   ollama pull phi3:mini
   ```

## 🏃 Running the Application

Start the server:
```bash
python app.py
```
The application will be available at `http://localhost:8000`.

## 🤝 Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to help improve this project.
