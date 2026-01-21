import pytesseract
from PIL import Image

# Set Tesseract path if it's not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def perform_ocr(image: Image, lang: str = "eng") -> str:
    """
    Perform OCR on a single PIL Image using Tesseract.
    Uses --psm 6 (Assume a single uniform block of text) as recommended.
    """
    try:
        # custom_config = r'--oem 3 --psm 6'
        # Using default config or user suggested --psm 6
        custom_config = r'--psm 6'
        text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
        return text
    except Exception as e:
        print(f"Error performing OCR: {e}")
        # Return empty string or re-raise depending on strictness
        return ""

def extract_text_from_images(images: list[Image]) -> str:
    """
    Iterate over a list of images and accumulate OCR text.
    """
    full_text = ""
    for i, img in enumerate(images):
        print(f"Processing page {i+1}...")
        text = perform_ocr(img)
        full_text += text + "\n"
    return full_text
