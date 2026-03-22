import os
import sys
import warnings
import json

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="urllib3")
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# Standard project root resolution
from tinyllama_service import extract_entities_ollama  # type: ignore # noqa: E402 # pylint: disable=import-error


def main():
    print("=== Testing Semantic Agentic Pipeline ===")
    test_pdf = "test_narrative.pdf"

    if not os.path.exists(test_pdf):
        print(f"Error: Could not find {test_pdf} to test.")
        return

    print(f"Executing pipeline on {test_pdf}...")
    result = extract_entities_ollama(test_pdf)

    print("\n=== FINAL OUTPUT SCHEMA ===")
    clean_dict = {
        k: v for k, v in result.items()
        if k != "pseudocode" and k != "metadata"
    }
    raw_json = json.dumps(clean_dict, indent=2)  # type: ignore
    print(raw_json[:1000] + "\n...[truncated]\n")
    print("=== PSEUDOCODE ===\n" + str(result.get("pseudocode", "")))
    print("\n=== METADATA ===\n" + str(result.get("metadata", "")))


if __name__ == "__main__":
    main()
