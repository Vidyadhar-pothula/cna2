# PDF Splitting Platform Walkthrough

## Overview
A local web application that allows you to upload a PDF and download two separate versions:
1.  **Text-Only PDF**: Contains only the text from the original document.
2.  **Images-Only PDF**: Contains only the images from the original document.

## How to Use

### 1. Start the Platform
Run the following command in your terminal:
```bash
python3 app.py
```
*Note: The server is already running in the background.*

### 2. Access the Interface
Open your web browser and navigate to:  
[http://127.0.0.1:5000](http://127.0.0.1:5000)

### 3. Split a Document
1.  Drag and drop your PDF file into the upload zone.
2.  Click **Split Document**.
3.  Once processed, click the **Download Text-Only** or **Download Images-Only** buttons to save your files.

## Technical Details
- **Backend**: Flask (Python)
- **PDF Processing**: PyMuPDF (fitz)
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism design)
- **Files**:
  - `app.py`: Main application logic.
  - `split_pdf.py`: PDF processing functions.
  - `templates/index.html`: User Interface.
  - `static/style.css`: Styling.
