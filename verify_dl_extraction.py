import os
import json
from dotenv import load_dotenv

# Load env vars BEFORE importing module that uses them
load_dotenv()

from llm_extractor import extract_all_documents, client
from PIL import Image

def verify_dl():
    image_path = "driving_licence_reference.jpg"
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    try:
        img = Image.open(image_path)
        images_with_filenames = [{"image": img, "filename": "driving_licence_reference.jpg"}]
        
        print("Sending image to LLM for extraction...")
        results = extract_all_documents(client, images_with_filenames)
        
        print(json.dumps(results, indent=2))
        
        # Validation checks
        if not results:
             print("FAILED: No results returned.")
             return

        doc = results[0]
        if doc.get("Document Type") == "Driving Licence":
             print("SUCCESS: Identified as Driving Licence.")
        else:
             print(f"FAILED: Document Type is {doc.get('Document Type')}")

        if doc.get("Address"):
             print(f"SUCCESS: Address extracted: {doc.get('Address')}")
        else:
             print("FAILED: Address not extracted.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_dl()
