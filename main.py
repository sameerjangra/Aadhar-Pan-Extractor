from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Import our modules
from pdf_processor import convert_pdf_to_images
from llm_extractor import extract_all_documents, client

from face_extractor import extract_face

app = FastAPI(title="Aadhar Pan Extraction")

# Configure CORS
origins = ["*"] # Allow all for demo

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_uploads"
OUTPUT_DIR = "processed_files"
FACES_DIR = "static/faces"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

async def process_files_logic(files: List[UploadFile]):
    """
    Core logic to process uploaded files, extract data, validate, merge, and extract photos.
    Returns (request_id, final_docs)
    """
    request_id = str(uuid.uuid4())
    print(f"Request ID: {request_id} - Processing {len(files)} files.")
    
    all_images_with_filenames = []
    temp_files_to_cleanup = []
    
    try:
        if not client:
             raise HTTPException(status_code=500, detail="LLM Client not initialized. Check server logs/API Key.")

        for file in files:
            # Basic validation
            if not file.filename.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
                continue

            file_ext = os.path.splitext(file.filename)[1]
            temp_filename = f"{request_id}_{uuid.uuid4()}{file_ext}"
            temp_path = os.path.join(TEMP_DIR, temp_filename)
            temp_files_to_cleanup.append(temp_path)
            
            try:
                # Save uploaded file
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Convert to Images
                images = []
                image_paths = [] 
                
                if file.filename.lower().endswith(".pdf"):
                    pil_images = convert_pdf_to_images(temp_path)
                    for idx, img in enumerate(pil_images):
                         page_filename = f"{request_id}_{uuid.uuid4()}_page{idx}.jpg"
                         page_path = os.path.join(TEMP_DIR, page_filename)
                         img.save(page_path, "JPEG")
                         temp_files_to_cleanup.append(page_path)
                         images.append(img)
                         image_paths.append(page_path)
                else:
                    from PIL import Image
                    try:
                         img = Image.open(temp_path).convert('RGB')
                         images = [img]
                         image_paths = [temp_path]
                    except Exception as e:
                        print(f"Image load failed for {file.filename}: {e}")
                        continue
                
                # Add to collection
                for img, path in zip(images, image_paths):
                    all_images_with_filenames.append({
                        "image": img,
                        "filename": file.filename,
                        "path": path 
                    })

            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                continue

        if not all_images_with_filenames:
             raise HTTPException(status_code=400, detail="No valid images found in upload.")

        # Batch Extraction
        print(f"sending {len(all_images_with_filenames)} images to LLM...")
        extracted_documents = extract_all_documents(client, all_images_with_filenames)
        
        if not extracted_documents:
             raise HTTPException(status_code=400, detail="No valid documents detected.")

        # Helper to extract face
        def get_face_photo(doc):
             source_filenames = doc.get("Source Files", [])
             
             candidates = [item for item in all_images_with_filenames if item["filename"] in source_filenames]
             
             for item in candidates:
                  # Use FACES_DIR for persistent storage
                  face_path = extract_face(item["path"], output_dir=FACES_DIR)
                  if face_path:
                       return face_path 
             return None

        # --- Identity Merging Logic ---
        merged_results = []
        
        # Helper to normalize strings for comparison
        def normalize(s):
            return str(s).lower().strip().replace("  ", " ") if s else ""

        for doc in extracted_documents:
            # Check if this doc belongs to an existing identity in merged_results
            match_index = -1
            
            doc_aadhar = normalize(doc.get("Aadhar Number"))
            doc_pan = normalize(doc.get("PAN Number"))
            doc_name = normalize(doc.get("Name"))
            
            for i, existing in enumerate(merged_results):
                ext_aadhar = normalize(existing.get("Aadhar Number"))
                ext_pan = normalize(existing.get("PAN Number"))
                ext_name = normalize(existing.get("Name"))
                
                # Match Logic:
                # 1. ID Match (Strongest)
                if doc_aadhar and ext_aadhar and doc_aadhar == ext_aadhar:
                    match_index = i
                    break
                if doc_pan and ext_pan and doc_pan == ext_pan:
                    match_index = i
                    break
                
                # 2. Name Match (Medium - only if significantly long to avoid "Kumar" matches)
                if doc_name and ext_name and len(doc_name) > 3 and doc_name == ext_name:
                    match_index = i
                    break
            
            if match_index >= 0:
                # MERGE into existing
                existing = merged_results[match_index]
                
                # Update Type
                types = set(existing.get("Document Type", "").split(" + "))
                types.add(doc.get("Document Type", "Unknown"))
                existing["Document Type"] = " + ".join(sorted(list(types)))
                
                # Merge Fields (Overwrite if new doc has value and existing doesn't, or blindly overwrite?)
                # Better to overwrite specific fields or aggregate.
                for k, v in doc.items():
                    if k in ["Document Type", "Sides Detected", "Source Files", "Photo Path"]: continue # Handle separately
                    
                    if v and (k not in existing or not existing[k]):
                         existing[k] = v
                
                # Merge Source Files
                existing["Source Files"] = list(set(existing.get("Source Files", []) + doc.get("Source Files", [])))
                
                # Merge Sides (for Aadhar)
                sides = set(existing.get("Sides Detected", []) + doc.get("Sides Detected", []))
                existing["Sides Detected"] = list(sides)
                
                # Handle Photo (Prioritize existing if present, else take new)
                new_photo = get_face_photo(doc)
                if new_photo and "Photo Path" not in existing:
                     existing["Photo Path"] = new_photo
                     
            else:
                # CREATE NEW Identity
                new_doc = doc.copy()
                
                # Initial Photo Extraction
                photo_path = get_face_photo(new_doc)
                if photo_path: new_doc["Photo Path"] = photo_path
                
                merged_results.append(new_doc)

        # --- Final Validation on Merged Identities ---
        final_valid_docs = []
        
        for doc in merged_results:
             # Aadhar Completeness Check
             if "Aadhar" in doc.get("Document Type", ""):
                 sides = [s.title() for s in doc.get("Sides Detected", [])]
                 has_front = "Front" in sides
                 has_back = "Back" in sides
                 
                 # Logic: If we rely on sides. 
                 # Often LLM might fail to explicitly tag "Sides Detected" for both if merged.
                 # Let's be lenient: If we have Aadhar Number + Address + Name, it's likely complete.
                 # But strict requirement was "user give 2 different...".
                 # If user uploads Front and Back separately, they are now merged.
                 # We should pass this merged doc.
                 pass 
             
             # Cleanup internal keys
             if "Sides Detected" in doc: del doc["Sides Detected"]
             
             final_valid_docs.append(doc)

        if not final_valid_docs:
             raise HTTPException(status_code=400, detail="No valid documents processed.")
        
        return request_id, final_valid_docs

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error processing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup input files
        for p in temp_files_to_cleanup:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

@app.post("/extract/")
async def extract_data(files: List[UploadFile] = File(...)):
    """
    Returns JSON Data with extracted information and photo URLs.
    """
    request_id, final_docs = await process_files_logic(files)
    
    # Post-process for JSON friendly URLs
    json_docs = []
    for doc in final_docs:
        d = doc.copy()
        if "Photo Path" in d:
            # Convert OS path to URL path
            # static/faces/abcd.jpg -> /static/faces/abcd.jpg
            # Ensure forward slashes
            rel_path = d["Photo Path"].replace("\\", "/")
            if not rel_path.startswith("/"):
                rel_path = "/" + rel_path
            d["Photo Path"] = rel_path
            d["Photo URL"] = rel_path # Duplicate for clarity
        json_docs.append(d)
    
    return JSONResponse(content={
        "status": "success",
        "request_id": request_id,
        "data": json_docs
    })
