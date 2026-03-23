from flask import Flask, request, jsonify, send_from_directory, render_template, send_file, flash, redirect, url_for, Response
from flask_cors import CORS
import os
import sys
import json
import uuid
import shutil
import threading
import time
from split_pdf import split_pdf
from dotenv import load_dotenv

# Add ml_prototype to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_prototype'))

# Compatibility patch for Python 3.9 and google-generativeai
try:
    import importlib.metadata as metadata
    if not hasattr(metadata, 'packages_distributions'):
        def packages_distributions():
            import importlib_metadata
            return importlib_metadata.packages_distributions()
        metadata.packages_distributions = packages_distributions
except ImportError:
    pass

# Load ENV consistently at top
load_dotenv()

# Imports for services at top
try:
    from tinyllama_service import extract_entities_ollama
except ImportError as e:
    print(f"Warning: tinyllama_service import failed: {e}")

# Try importing ML modules, warn if missing
try:
    from layoutlmv3_extractor import load_model, preprocess_document, run_inference, structure_output, LABELS_MAP
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML module import failed: {e}")
    ML_AVAILABLE = False

# Check for poppler
if shutil.which('pdftoppm') is None:
    print("WARNING: 'pdftoppm' (poppler) not found in PATH.")

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.getcwd(), 'processed')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Global Job Store
JOBS: dict = {}
MODEL_LOCK = threading.Lock()
model = None
processor = None

def get_ml_model():
    global model, processor, ML_AVAILABLE
    if not ML_AVAILABLE: return None, None
    with MODEL_LOCK:
        if model is None:
            print("[ML] Loading Model (Lazy)...")
            try:
                from layoutlmv3_extractor import load_model as lm_load
                model, processor = lm_load()
                print("[ML] Model Loaded!")
            except Exception as e:
                print(f"[ML] Failed to load: {e}")
                ML_AVAILABLE = False
        return model, processor

# --- Normalization Helper ---
def normalize_extraction_result(raw_result):
    """Normalizes raw extraction JSON into a strict table schema."""
    normalized = {
        "equipment_table": [],
        "parameters_table": [],
        "variables_table": [],
        "conditions_table": [],
        "actions_table": [],
        "unified_control_table": raw_result.get("unified_control_table", []),
        "pseudocode": raw_result.get("pseudocode", "")
    }
    if not raw_result: return normalized
    
    mapping = {
        "equipment": "equipment_table",
        "parameters": "parameters_table",
        "variables": "variables_table",
        "conditions": "conditions_table",
        "actions": "actions_table"
    }
    for raw_key, table_key in mapping.items():
        items = raw_result.get(raw_key, [])
        if isinstance(items, list):
            for idx, item in enumerate(items):
                normalized[table_key].append({
                    "id": item.get("id", f"{raw_key[:3].upper()}-{idx+1:02}"),
                    "name": item.get("name") or item.get("condition") or item.get("action") or "Unnamed",
                    "description": item.get("description") or item.get("value") or "No description"
                })
    return normalized

# --- Routes ---

@app.route('/')
def index():
    print("[Route] GET /")
    return render_template('index.html')

@app.route('/analysis')
def analysis():
    print("[Route] GET /analysis")
    return render_template('index.html')

@app.route('/splitter')
def splitter_index():
    return redirect(url_for('index'))

@app.route('/api/process_document', methods=['POST'])
def process_document_api():
    # Legacy ML_AVAILABLE check removed as we now use the Ollama semantic pipeline
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    temp_path = os.path.join('ml_prototype', 'temp_upload.pdf')
    file.save(temp_path)
    try:
        # Use the NEW semantic pipeline instead of the legacy LayoutLM block
        raw_result = extract_entities_ollama(temp_path)
        
        if raw_result and "error" not in raw_result:
            # Normalize for the frontend which expects specific keys in this endpoint
            return jsonify({
                "equipment": raw_result.get("equipment_table", []),
                "variables": raw_result.get("variables_table", []),
                "parameters": raw_result.get("parameters_table", []),
                "conditions": raw_result.get("conditions_table", []),
                "actions": raw_result.get("actions_table", []),
                "unified_control_table": raw_result.get("unified_control_table", []),
                "pseudocode": raw_result.get("pseudocode", ""),
                "metadata": {
                    "engine": "ORION Semantic Pipeline (Sequential)",
                    "model": "qwen2.5:14b"
                }
            })
        else:
            return jsonify({"error": raw_result.get("error") if raw_result else "Extraction failed"}), 500
    except Exception as e:
        print(f"Error in process_document_api: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload_split', methods=['POST'])
def upload_file_split():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No filename"}), 400
    
    session_id = str(uuid.uuid4())
    session_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    session_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    os.makedirs(session_output_dir, exist_ok=True)
    
    file_path = os.path.join(session_upload_dir, file.filename)
    file.save(file_path)
    JOBS[session_id] = {"status": "processing"}
    
    def worker():
        try:
            print(f"[Worker] Processing {session_id}...")
            text_pdf, images_pdf = split_pdf(file_path, output_folder=session_output_dir)
            raw_result = extract_entities_ollama(text_pdf)
            
            if raw_result and "error" not in raw_result:
                if "equipment_table" in raw_result:
                    norm = raw_result
                else:
                    norm = normalize_extraction_result(raw_result)
                JOBS[session_id] = {
                    "status": "completed",
                    "session_id": session_id,
                    "text_filename": "text_only.pdf",
                    "images_filename": "images_only.pdf",
                    "extraction_result": raw_result,
                    "normalized_tables": norm
                }
            else:
                JOBS[session_id] = {"status": "failed", "error": raw_result.get("error") if raw_result else "Unknown"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            JOBS[session_id] = {"status": "failed", "error": str(e)}

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"success": True, "session_id": session_id})

@app.route('/api/job_status/<session_id>')
def job_status(session_id):
    return jsonify(JOBS.get(session_id, {"status": "not_found"}))

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """
    Chat endpoint proxying to local Ollama (Qwen 2.5 14B).
    Accepts: { messages: [], system: "" }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        from langchain_ollama import OllamaLLM
        # Use existing model constants from tinyllama_service if possible, 
        # or just hardcode for speed here as it's the verified model.
        llm = OllamaLLM(model="qwen2.5:14b", temperature=0.2)
        
        messages = data.get('messages', [])
        system_prompt = data.get('system', '')
        
        # Combine into a single prompt for standard OllamaLLM call
        full_prompt = f"System: {system_prompt}\n\n"
        for msg in messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            full_prompt += f"{role}: {msg['content']}\n"
        full_prompt += "Assistant: "
        
        response_text = llm.invoke(full_prompt)
        
        # Structure response to match what the frontend expects (Claude-like format)
        return jsonify({
            "content": [{"type": "text", "text": response_text}]
        })
    except Exception as e:
        print(f"[Chat API] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download_split/<session_id>/<filename>')
def download_file_split(session_id, filename):
    directory = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    return send_file(os.path.join(directory, filename), as_attachment=True)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    print("ORION Server starting on http://127.0.0.1:8000")
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
