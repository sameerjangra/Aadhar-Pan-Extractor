import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add current directory to sys.path to ensure imports work
sys.path.append(os.getcwd())

from pdf_processor import convert_pdf_to_images
from ocr_engine import extract_text_from_images
from text_cleaner import clean_ocr_text
from llm_extractor import extract_data_with_llm

def test_pipeline(pdf_path):
    print(f"--- Starting Test Pipeline for {pdf_path} ---")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    # 1. Convert to Images
    print("1. Converting PDF to Images (PyMuPDF)...")
    try:
        images = convert_pdf_to_images(pdf_path)
        print(f"   Success: Converted to {len(images)} images.")
    except Exception as e:
        print(f"   Failed: {e}")
        return

    # 4. LLM Extraction (Vision)
    print("2. LLM Extraction (Groq meta-llama/llama-4-maverick-17b-128e-instruct)...")
    if not os.environ.get("GROQ_API_KEY"):
        print("   Warning: GROQ_API_KEY not found in environment. Skipping actual API call.")
    else:
        try:
            # We now pass images directly
            data = extract_data_with_llm(images)
            print(f"   Success: {data}")
        except Exception as e:
            print(f"   Failed: {e}")

    print("--- Test Complete ---")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default path if no argument provided
        pdf_path = os.path.abspath(os.path.join(os.getcwd(), "..", "insurance-extractor", "data", "raw_pdfs", "Policy_0001.pdf"))
    
    test_pipeline(pdf_path)
