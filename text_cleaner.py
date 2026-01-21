import re

def clean_ocr_text(text: str) -> str:
    """
    Clean raw OCR text by removing excessive newlines and non-printable characters.
    """
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    # Remove non-ASCII characters (optional, depending on requirements, but often good for noise)
    # Keeping basic punctuation and alphanumeric.
    # The user suggested: re.sub(r'[^\x00-\x7F]+', ' ', text) which keeps ASCII.
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()
