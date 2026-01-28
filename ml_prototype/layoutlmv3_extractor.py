import torch
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor
from pdf2image import convert_from_path
from PIL import Image
import json
import os

# --- Configuration ---
# In a real scenario, these labels must match your fine-tuned model's config
LABELS_MAP = {
    0: "O",
    1: "B-EQUIPMENT",
    2: "I-EQUIPMENT",
    3: "B-VARIABLE",
    4: "I-VARIABLE",
    5: "B-PARAMETER",
    6: "I-PARAMETER"
}

MODEL_ID = "microsoft/layoutlmv3-base"

def normalize_bbox(bbox, width, height):
    """
    Normalize bounding box coordinates to 0-1000 scale.
    bbox: [x0, y0, x1, y1]
    """
    return [
        int(1000 * (bbox[0] / width)),
        int(1000 * (bbox[1] / height)),
        int(1000 * (bbox[2] / width)),
        int(1000 * (bbox[3] / height)),
    ]

def load_model():
    print(f"Loading model: {MODEL_ID}...")
    # Note: Using num_labels to initialize the classification head. 
    # Without fine-tuning, predictions will be random/untrained.
    model = LayoutLMv3ForTokenClassification.from_pretrained(MODEL_ID, num_labels=len(LABELS_MAP))
    # CRITICAL: Set apply_ocr=False because we are providing our own words/boxes
    processor = LayoutLMv3Processor.from_pretrained(MODEL_ID, apply_ocr=False)
    return model, processor

def preprocess_document(pdf_path, processor):
    print(f"Processing document: {pdf_path}")
    
    # 1. PDF to Image
    # Requires poppler installed on the system
    try:
        images = convert_from_path(pdf_path)
    except Exception as e:
        print(f"Error converting PDF: {e}")
        print("Ensure 'poppler' is installed (e.g., 'brew install poppler' on Mac).")
        return None, None, None

    if not images:
        print("No images converted from PDF.")
        return None, None, None

    image = images[0].convert("RGB") # Take first page
    width, height = image.size

    # 2. OCR Emulation (Mock Data for Prototype)
    # In production, use pytesseract.image_to_data(image)
    print("Emulating OCR...")
    words = ["SUSV", "Flow", "Rate", "Tolerance", "P-101", "Incoming", "Flow", "Rate"]
    
    # Mock Bounding Boxes [x0, y0, x1, y1] (Unnormalized)
    raw_boxes = [
        [100, 100, 200, 150], # SUSV
        [210, 100, 300, 150], # Flow
        [310, 100, 400, 150], # Rate
        [100, 200, 300, 250], # Tolerance
        [400, 400, 500, 450], # P-101
        [100, 500, 200, 550], # Incoming
        [210, 500, 300, 550], # Flow
        [310, 500, 400, 550]  # Rate
    ]

    # Normalize Boxes
    boxes = [normalize_bbox(box, width, height) for box in raw_boxes]

    # 3. Tokenization & Encoding
    print("Tokenizing...")
    encoding = processor(
        images=image,
        text=words,
        boxes=boxes,
        return_tensors="pt",
        truncation=True,
        padding="max_length"
    )

    return encoding, words, boxes

def run_inference(model, encoding):
    print("Running inference...")
    model.eval()
    with torch.no_grad():
        outputs = model(**encoding)
    
    # Get Logits and Predictions
    logits = outputs.logits
    predictions = logits.argmax(-1).squeeze().tolist()
    
    return predictions

def structure_output(words, boxes, predictions, id2label):
    print("Structuring output...")
    structured_data = []
    
    # Iterate through tokens
    # Note: encoding length might differ from word length due to sub-word tokenization.
    # For this prototype, we assume 1-to-1 mapping for simplicity.
    
    for i, (word, box, pred_id) in enumerate(zip(words, boxes, predictions)):
        label = id2label.get(pred_id, "O")
        
        # In a real app, you might filter out 'O' labels to reduce noise
        entry = {
            "token": word,
            "bbox": box,
            "label": label,
            "confidence": 0.99 # Placeholder
        }
        structured_data.append(entry)
            
    return structured_data

def main():
    # Create a dummy PDF if it doesn't exist for testing
    pdf_path = "sample_document.pdf"
    if not os.path.exists(pdf_path):
        print(f"Note: '{pdf_path}' not found. Please place a valid PDF in this directory.")
        print("For testing purposes, ensure you have a PDF named 'sample_document.pdf'.")
        return

    model, processor = load_model()
    encoding, words, boxes = preprocess_document(pdf_path, processor)
    
    if encoding is None:
        return

    predictions = run_inference(model, encoding)
    
    # Align predictions (Simplified)
    aligned_predictions = predictions[:len(words)]
    
    result = structure_output(words, boxes, aligned_predictions, LABELS_MAP)
    
    # Output JSON
    output_json = json.dumps(result, indent=2)
    print("\n--- Final Structured Output ---")
    print(output_json)
    
    # Save to file
    with open("output.json", "w") as f:
        f.write(output_json)
    print("\nOutput saved to output.json")

if __name__ == "__main__":
    main()
