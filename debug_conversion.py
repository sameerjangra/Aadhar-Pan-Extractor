import os
import sys
from pdf_processor import convert_pdf_to_images

# Mock the PDF path - I'll try to find a PDF in the parent directory as before or create a dummy one
# Actually, I'll search for a PDF first.
def test_conversion():
    # Try to find a PDF
    pdf_path = ""
    # Check common locations
    possible_paths = [
        r"c:\Users\intern.it2\.gemini\antigravity\scratch\insurance-extractor\data\raw_pdfs\Policy_0001.pdf",
        r"c:/Users/intern.it2/.gemini/antigravity/scratch/insurance-extractor/data/raw_pdfs/Policy_0001.pdf"
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            pdf_path = p
            break
            
    if not pdf_path:
        print("No PDF found to test. Please place a 'test.pdf' in this folder.")
        return

    print(f"Testing conversion on: {pdf_path}")
    images = convert_pdf_to_images(pdf_path)
    print(f"Converted {len(images)} images.")
    
    if len(images) > 0:
        print(f"First image size: {images[0].size}")
        try:
            images[0].save("debug_test_image.png")
            print("Saved debug_test_image.png")
        except Exception as e:
            print(f"Failed to save image: {e}")

if __name__ == "__main__":
    test_conversion()
