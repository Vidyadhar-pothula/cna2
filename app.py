from flask import Flask, request, jsonify, send_from_directory, render_template, send_file, flash, redirect, url_for
from flask_cors import CORS
import os
import sys
import json
import uuid
import shutil
from split_pdf import split_pdf

# Add ml_prototype to path so we can import the extractor
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_prototype'))

# Try importing ML modules, warn if missing
try:
    from layoutlmv3_extractor import load_model, preprocess_document, run_inference, structure_output, LABELS_MAP
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML module import failed: {e}")
    ML_AVAILABLE = False

# Check for poppler
if shutil.which('pdftoppm') is None:
    print("WARNING: 'pdftoppm' (poppler) not found in PATH. PDF processing will fail.")

app = Flask(__name__, static_folder='.', template_folder='templates')
app.secret_key = 'supersecretkey'
CORS(app)

# Configuration for Splitter
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.getcwd(), 'processed')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Load model once at startup if available
if ML_AVAILABLE:
    print("Loading LayoutLMv3 Model...")
    try:
        model, processor = load_model()
        print("Model Loaded!")
    except Exception as e:
        print(f"Failed to load model: {e}")
        ML_AVAILABLE = False

# --- Routes for Existing LayoutLMv3 App ---

@app.route('/')
def index():
    return render_template('splitter.html')

@app.route('/analysis')
def analysis():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    # Avoid serving templates/static through this catch-all if possible, 
    # but since static_folder='.', it might catch everything.
    # Flask matches explicit routes first.
    return send_from_directory('.', path)

@app.route('/api/process_document', methods=['POST'])
def process_document_api():
    if not ML_AVAILABLE:
        return jsonify({"error": "ML Model not available"}), 503

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        temp_path = os.path.join('ml_prototype', 'temp_upload.pdf')
        file.save(temp_path)
        
        try:
            encoding, words, boxes = preprocess_document(temp_path, processor)
            if encoding is None:
                return jsonify({"error": "Failed to process PDF"}), 500

            predictions = run_inference(model, encoding)
            aligned_predictions = predictions[:len(words)]
            result = structure_output(words, boxes, aligned_predictions, LABELS_MAP)
            return jsonify(result)
        except Exception as e:
            print(f"Error processing document: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/splitter')
def splitter_index():
    return redirect(url_for('index'))

# --- Routes for Gemini/TinyLlama Extraction ---

# from gemini_service import extract_entities  <-- Removed
from tinyllama_service import extract_entities_ollama

# Load environment variables (Still useful for other things, but not for API key now)
from dotenv import load_dotenv
load_dotenv()

@app.route('/upload_split', methods=['POST'])
def upload_file_split():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('splitter_index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('splitter_index'))
    
    if file and file.filename.lower().endswith('.pdf'):
        session_id = str(uuid.uuid4())
        session_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        session_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        
        os.makedirs(session_upload_dir, exist_ok=True)
        os.makedirs(session_output_dir, exist_ok=True)
        
        file_path = os.path.join(session_upload_dir, file.filename)
        file.save(file_path)
        
        try:
            # 1. Split PDF
            text_pdf, images_pdf = split_pdf(file_path, output_folder=session_output_dir)
            
            # 2. Extract Entities via TinyLlama (Local) - using the Text-Only PDF
            try:
                # Pass the path to the text-only PDF
                extraction_result = extract_entities_ollama(text_pdf)
                import json
                print(f"DEBUG: Extraction Result for {session_id}:")
                print(json.dumps(extraction_result, indent=2))
            except Exception as ml_err:
                print(f"TinyLlama Extraction failed: {ml_err}")
                extraction_result = {"error": str(ml_err)}

            return render_template('splitter.html', 
                                   result=True, 
                                   session_id=session_id,
                                   text_filename="text_only.pdf",
                                   images_filename="images_only.pdf",
                                   extraction_result=extraction_result)
                                   
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('splitter_index'))
            
    else:
        flash('Invalid file type. Please upload a PDF.')
        return redirect(url_for('splitter_index'))

@app.route('/download_split/<session_id>/<filename>')
def download_file_split(session_id, filename):
    directory = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    return send_file(os.path.join(directory, filename), as_attachment=True)

if __name__ == '__main__':
    # Use port 8000 to match previous config, or 5000? 
    # Remote used 8000. Let's stick to 8000.
    app.run(port=8000, debug=True)
