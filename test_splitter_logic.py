
import os
from reportlab.pdfgen import canvas
from tinyllama_service import extract_entities_ollama
from split_pdf import split_pdf

def create_dummy_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "Control Narrative")
    c.drawString(100, 700, "If Level > 80% then Start Pump P-101.")
    c.drawString(100, 680, "The Water_Tank (T-100) must be monitored.")
    c.save()
    print(f"Created {filename}")

def test_pipeline():
    # 1. Create PDF
    pdf_path = "test_narrative.pdf"
    create_dummy_pdf(pdf_path)
    
    # 2. Test Splitter
    print("\n--- Testing Splitter ---")
    try:
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)
        text_pdf, images_pdf = split_pdf(pdf_path, output_dir)
        print(f"Split successful: {text_pdf}, {images_pdf}")
    except Exception as e:
        print(f"Splitter failed: {e}")
        return

    # 3. Test Extraction (Ollama + Agentic Prompt)
    print("\n--- Testing Extraction (Agentic + Ollama) ---")
    print("Step 1: The Agent will generate a specific prompt based on the content.")
    print("Step 2: The Executor will use that prompt to extract data.")
    try:
        result = extract_entities_ollama(text_pdf)
        print("\nFinal Extraction Result:")
        print(result)
        
        if "error" in result:
            print("FAIL: Extraction returned error.")
        else:
            print("SUCCESS: Extraction returned data.")
            if result.get("equipment") or result.get("actions"):
                print("SUCCESS: Found entities.")
            else:
                 print("WARNING: Valid JSON but empty entities (Model might need tuning).")
            
    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    test_pipeline()
