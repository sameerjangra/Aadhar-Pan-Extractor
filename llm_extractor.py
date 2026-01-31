import os
import json
import base64
import io
from typing import Dict, Any, List, Optional
from openai import OpenAI
from PIL import Image

# Initialize client responsibly
groq_key = os.environ.get("GROQ_API_KEY")

if groq_key:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_key
    )
else:
    print("Warning: GROQ_API_KEY is missing from environment variables.")
    client = None

def encode_image(image: Image.Image) -> str:
    """Encodes a PIL Image to a base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_all_documents(client: OpenAI, images_with_filenames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes all images together and extracts unique documents, merging Front/Back based on ID.
    """
    prompt = """
    Analyze the provided images of Aadhar, PAN cards, and Driving Licences. Your goal is to extract structured data for each unique document.

    **CRITICAL INSTRUCTIONS**:
    1. **Aadhar**: 
       - If you see Aadhar Front and Back for the same person, COMBINE them into a single record.
       - **NEW FIELD**: `Sides Detected`. This must be a LIST of strings: ["Front"], ["Back"], or ["Front", "Back"]. Check the visual content to decide.
       - Extract: Name, DOB, Gender, Aadhar Number, Address (from back).

    2. **PAN & Driving Licence (DL)**:
       - **DO NOT MERGE PAN AND DL**. Keep them as SEPARATE records even if they belong to the same person.
       - **PAN**: Extract Name, Father Name, DOB, PAN Number.
       - **Driving Licence**: Extract Name, DL Number, Address (Look for "S/W/D", "Add", "Address").

    **Fields to Extract**:
    - Document Type ("Aadhar", "PAN", "Driving Licence")
    - Name
    - Father Name (for PAN)
    - Date of Birth (YYYY-MM-DD)
    - Gender (for Aadhar)
    - Aadhar Number (12 digits)
    - PAN Number (10 alphanumeric)
    - DL Number (for Driving Licence)
    - Address (Full address from Aadhar back or Driving Licence)
    - Sides Detected (List of ["Front", "Back"] - ONLY for Aadhar)
    - Source Files (List of filenames)

    **Validation**:
    - If a document is NOT Aadhar, PAN, or Driving Licence, ignore it.
    - Do NOT return empty records.

    Return a JSON object with a key "documents" containing a LIST of extracted records.
    Example Output:
    {
        "documents": [
            {
                "Document Type": "Aadhar",
                "Name": "Ravi Kumar",
                "Sides Detected": ["Front", "Back"],
                "Aadhar Number": "1234 5678 9012"
            },
            {
                "Document Type": "PAN",
                "Name": "Atul Kumar",
                "Father Name": "Suresh Kumar",
                "PAN Number": "ABCD1234E"
            },
            {
                "Document Type": "Driving Licence",
                "Name": "Atul Kumar",
                "DL Number": "HR01 20000000856",
                "Address": "FLAT NO 401..."
            }
        ]
    }
    """
    
    try:
        content_parts = [{"type": "text", "text": prompt}]
        
        # Limit total images to avoid payload issues, but user usually uploads 2-4
        for item in images_with_filenames[:10]: 
            img = item["image"]
            filename = item["filename"]
            base64_image = encode_image(img)
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            })
            content_parts.append({
                "type": "text", 
                "text": f"Above image is from file: {filename}"
            })
            
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": content_parts}],
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = chat_completion.choices[0].message.content
        data = json.loads(content)
        return data.get("documents", [])
        
    except Exception as e:
        print(f"Error in batch extraction: {e}")
        return []

# Helper / Legacy wrappers if needed, but we will likely call extract_all_documents directly

