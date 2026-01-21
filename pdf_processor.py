import os
import fitz  # PyMuPDF
from PIL import Image
import io

def convert_pdf_to_images(pdf_path: str) -> list[Image.Image]:
    """
    Convert a PDF file to a list of PIL Images using PyMuPDF (fitz).
    This removes the dependency on Poppler.
    """
    images = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom=2 for better resolution
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        return images
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []
        