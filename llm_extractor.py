import os
import json
import base64
import io
from typing import Dict, Any, List
from openai import OpenAI
from PIL import Image

# Initialize client responsibly
# We expect GROQ_API_KEY to be in environment variables.
groq_key = os.environ.get("GROQ_API_KEY")

if groq_key:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_key
    )
else:
    print("Warning: GROQ_API_KEY is missing from environment variables.")
    client = None

SYSTEM_PROMPT = """You are an insurance policy analysis assistant.
You will be provided with images of an insurance policy.
Extract the following exact fields from the policy document:

- Insured (Name of the policy holder)
- Business/Profession
- Address of The Insured
- TP Policy Period (Third Party Liability Period)
- Vehicle Regn No (Registration Number)
- Engine No  
- Chassis No.
- Make & Model
- Year of Mfg (Manufacture Year)
- Cubic Capacity
- Declared Value (IDV) of Vehicle
- Total IDV
- Premium (Total Premium)
- Nominee Name
- Nominee Age
- Nominee Relation

Rules:
- If a field is missing, return null
- Normalize dates to YYYY-MM-DD
- Return ONLY valid JSON with keys corresponding exactly to the field names above (snake_case preferred for keys).

Specific Field Instructions:
- **Make & Model**: capture the FULL Make and Model string found. It often includes the manufacturer (e.g., "Hero MotoCorp") and the variant (e.g., "SPLENDOR PRO DRK CCR"). Do not truncate.
- **Chassis No.**: Look for a long alphanumeric string, often starting with "MBL..." or similar manufacturer codes. Ensure you capture the full string (e.g. "MBLHA10ABIKW65550").
- **Engine No**: Look for the engine serial number (e.g., "HA10ABIKW65550"). Be careful not to confuse '0' (zero) and 'O' (letter O).
- **TP Policy Period**: Ensure you capture the correct Start and End dates for the Third Party period.
- **Vehicle Regn No**: Look for the registration number (e.g., DL-01-AB-1234). If the vehicle is new, it may be marked as "NEW" or "TO BE GENERATED". **Do NOT** confuse this with parts of the model name (like "DRK").

Expected JSON Structure:
{
  "Insured": "...",
  "Business/Profession": "...",
  "Address of The Insured": "...",
  "TP Policy Period": "...",
  "Vehicle Regn No": "...",
  "Engine No": "...",
  "Chassis No.": "...",
  "Make & Model": "...",
  "Year of Mfg": "...",
  "Cubic Capacity": "...",
  "Declared Value (IDV) of Vehicle": "...",
  "Total IDV": "...",
  "Premium": "...",
  "Nominee Name": "...",
  "Nominee Age": "...",
  "Nominee Relation": "..."
}
"""

def encode_image(image: Image.Image) -> str:
    """Encodes a PIL Image to a base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_data_with_llm(images: List[Image.Image]) -> Dict[str, Any]:
    """
    Send the policy images to Groq for extraction.
    """
    global client
    
    if not images:
        return {}
    
    if not client:
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key
            )
        else:
             print("Error: GROQ_API_KEY missing.")
             return {}

    try:
        # Prepare content: Text prompt + Images
        content_parts = [{"type": "text", "text": SYSTEM_PROMPT}]
        
        # Add up to 5 images
        for img in images[:5]:
            base64_image = encode_image(img)
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            })
            
        content_parts.append({"type": "text", "text": "Generate the JSON response based on the above images."})

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": content_parts,
                }
            ],
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            response_format={"type": "json_object"},
        )
        
        content = chat_completion.choices[0].message.content
        print(f"DEBUG: Raw Groq Response: {content}") 
        
        if not content:
            raise Exception("Groq returned empty content")
            
        data = json.loads(content)
        return data

    except Exception as e:
        print(f"Error calling Groq: {e}")
        # Re-raise so the main app knows it failed
        raise e
