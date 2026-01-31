import os
from PIL import Image
from llm_extractor import extract_all_documents, client
import json
from dotenv import load_dotenv

load_dotenv()

# Paths to the uploaded images
image_path_1 = r"C:/Users/intern.it2/.gemini/antigravity/brain/2dc8796a-01ad-4ca1-99d7-d084e6c7e64a/uploaded_media_0_1769770562341.png"
image_path_2 = r"C:/Users/intern.it2/.gemini/antigravity/brain/2dc8796a-01ad-4ca1-99d7-d084e6c7e64a/uploaded_media_1_1769770562341.png"

def verify():
    print("Loading images...")
    images_input = []
    
    if os.path.exists(image_path_1):
        try:
            img1 = Image.open(image_path_1).convert('RGB')
            images_input.append({"image": img1, "filename": "front.png"})
            print(f"Loaded {image_path_1}")
        except Exception as e:
            print(f"Failed to load image 1: {e}")

    if os.path.exists(image_path_2):
        try:
            img2 = Image.open(image_path_2).convert('RGB')
            images_input.append({"image": img2, "filename": "back.png"})
            print(f"Loaded {image_path_2}")
        except Exception as e:
            print(f"Failed to load image 2: {e}")

    if not images_input:
        print("No images loaded.")
        return

    print("Running extraction...")
    try:
        # The extractor expects a list of dicts with 'image' and 'filename'
        result = extract_all_documents(client, images_input)
        print("\n--- Extraction Result ---")
        print(json.dumps(result, indent=4))
    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    verify()
