import fitz
import sys
import os

def split_pdf(input_path, output_folder=None):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File {input_path} not found.")

    input_path = os.path.abspath(input_path)
    if output_folder:
        base_dir = output_folder
    else:
        base_dir = os.path.dirname(input_path)
    
    # Create output filename based on input filename to avoid collisions if needed, 
    # but for this simple app, fixed names in a unique session folder might be better.
    # Let's stick to simple names for now, relying on the caller to manage folders.
    text_output = os.path.join(base_dir, "text_only.pdf")
    images_output = os.path.join(base_dir, "images_only.pdf")

    # Generate Text-Only PDF
    # Strategy: Remove image objects (raster) but keep vector drawings (table lines).
    try:
        doc_text = fitz.open(input_path)
        for page in doc_text:
            # Get all images on the page
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                page.delete_image(xref)
        doc_text.save(text_output)
        doc_text.close()
    except Exception as e:
        print(f"Error creating text_only.pdf: {e}")
        text_output = None

    # Generate Images-Only PDF
    # Strategy: Create fresh pages and re-insert ONLY the images found in the original.
    # This prevents table borders (vector drawings) and text residue from appearing.
    try:
        doc_src = fitz.open(input_path)
        doc_images = fitz.open() # New empty PDF
        
        for page in doc_src:
            # Create a new page with the same dimensions
            new_page = doc_images.new_page(width=page.rect.width, height=page.rect.height)
            
            # Get detailed image info including bounding boxes
            image_infos = page.get_image_info(xrefs=True)
            
            for img in image_infos:
                xref = img['xref']
                bbox = fitz.Rect(img['bbox'])
                
                # Extract image data
                try:
                    # We can use the binary stream directly if possible, or extract
                    img_data = doc_src.extract_image(xref)
                    if img_data:
                        # Insert content onto new page at exact location
                        new_page.insert_image(bbox, stream=img_data["image"])
                except Exception as img_err:
                    print(f"Warning: Could not extract/insert image {xref}: {img_err}")
                    
        doc_images.save(images_output)
        doc_images.close()
        doc_src.close()
    except Exception as e:
        print(f"Error creating images_only.pdf: {e}")
        # Fallback to redaction if reconstruction fails? 
        # For now, let's assume reconstruction works or fail hard.
        # But wait, we caught the exception.
        images_output = None
        
    return text_output, images_output

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_pdf.py <input_pdf>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    t, i = split_pdf(input_file)
    print(f"Text PDF: {t}")
    print(f"Images PDF: {i}")
