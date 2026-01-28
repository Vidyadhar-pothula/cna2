# Contributing to LayoutLMv3 Data Flow Simulation

Thank you for your interest in contributing! We welcome contributions to improve the entity extraction pipeline, UI, and overall stability.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/control-narrative-analysis.git
    cd control-narrative-analysis
    ```
3.  **Set up the environment**:
    - Ensure you have Python 3.9+ installed.
    - Install dependencies (we recommend a virtual environment):
      ```bash
      pip install -r requirements.txt
      ```
4.  **Install/Update Ollama**:
    - This project relies on [Ollama](https://ollama.com/) for local LLM inference.
    - Pull the required model:
      ```bash
      ollama pull phi3:mini
      ```

## Development Workflow

1.  **Create a branch** for your feature or fix:
    ```bash
    git checkout -b feature/my-new-feature
    ```
2.  **Make your changes**.
3.  **Test your changes**:
    - Run the pipeline verification script:
      ```bash
      python3 test_splitter_logic.py
      ```
    - Ensure the direct model test passes:
      ```bash
      python3 test_phi3_direct.py
      ```

## Submitting a Pull Request

1.  Push your branch to your fork.
2.  Open a Pull Request (PR) against the `main` branch.
3.  Describe your changes clearly in the PR description.
4.  Wait for review!

## Code Style

- Please keep code readable and well-commented.
- Follow existing patterns in `tinyllama_service.py` for LLM interaction.
- Ensure all new dependencies are added to `requirements.txt`.
