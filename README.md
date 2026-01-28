# Control Narrative Analysis with LayoutLMv3 & Phi-3

A local-first document intelligence pipeline for extracting structured entities (Equipment, Parameters, Variables, Conditions, Actions) from Industrial Control Narrative PDFs.

## core Technology

-   **Structure Analysis**: [LayoutLMv3](https://github.com/microsoft/unilm/tree/master/layoutlmv3) (Local Inference)
-   **Entity Extraction**: [Phi-3 Mini](https://ollama.com/library/phi3) (via Ollama)
-   **Backend**: Flask + LangChain
-   **Frontend**: HTML/JS Table Visualization

## Features

-   **100% Local Privacy**: No data leaves your machine.
-   **Split Processing**: Automatically separates text logic from P&ID diagrams.
-   **Balanced Single-Pass Architecture**: Uses a neutral, agentic controller to orchestrate Phi-3 for complete, unbiased entity extraction in one pass.
-   **Strict Schema**: Enforces output suitable for ISA-88 documentation usage.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Vidyadhar-pothula/control-narrative-analysis.git
    cd control-narrative-analysis
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Ollama**:
    -   Install [Ollama](https://ollama.com/).
    -   Pull the model:
        ```bash
        ollama pull phi3:mini
        ```

## Usage

1.  Start the Ollama backend:
    ```bash
    ollama serve
    ```

2.  Run the Application:
    ```bash
    python3 app.py
    ```

3.  Open browser to `http://localhost:8000`.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.
