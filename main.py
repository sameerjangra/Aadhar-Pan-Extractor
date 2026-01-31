from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import uuid
from dotenv import load_dotenv
 
load_dotenv()

# Import our modules
from pdf_processor import convert_pdf_to_images
from llm_extractor import extract_all_documents, client # Import new function at top level
from data_exporter import export_to_excel

app = FastAPI(title="Aadhar Pan Extraction")

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_uploads"
OUTPUT_DIR = "processed_files"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=False) if not os.path.exists(OUTPUT_DIR) else None

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

from typing import List

@app.post("/extract/")
async def extract_data(files: List[UploadFile] = File(...)):
    """
    Upload multiple PDF/Image files (Aadhar/PAN), classify & extract data, and return an Excel file.
    """
    request_id = str(uuid.uuid4())
    print(f"Request ID: {request_id} - Processing {len(files)} files.")
    
    # 1. Collect all images
    all_images_with_filenames = []
    
    
    # Track temp files for cleanup
    temp_files_to_cleanup = []
    
    try:
        if not client:
             raise HTTPException(status_code=500, detail="LLM Client not initialized. Check server logs/API Key.")

        from face_extractor import extract_face

        for file in files:
            # Basic validation
            if not file.filename.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
                continue

            # Original upload path
            file_ext = os.path.splitext(file.filename)[1]
            temp_filename = f"{request_id}_{uuid.uuid4()}{file_ext}"
            temp_path = os.path.join(TEMP_DIR, temp_filename)
            temp_files_to_cleanup.append(temp_path)
            
            try:
                # Save uploaded file
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Convert to Images (and save them as temp files for face extraction)
                images = []
                image_paths = [] # Store paths corresponding to images
                
                if file.filename.lower().endswith(".pdf"):
                    pil_images = convert_pdf_to_images(temp_path)
                    for idx, img in enumerate(pil_images):
                         # Save each page as image
                         page_filename = f"{request_id}_{uuid.uuid4()}_page{idx}.jpg"
                         page_path = os.path.join(TEMP_DIR, page_filename)
                         img.save(page_path, "JPEG")
                         temp_files_to_cleanup.append(page_path)
                         images.append(img)
                         image_paths.append(page_path)
                else:
                    # It's already an image, just ensure it's RGB
                    from PIL import Image
                    try:
                         # We already saved it to temp_path. Let's verify it opens.
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
                        "filename": file.filename, # Original user filename for LLM context
                        "path": path # Local temp path for face extraction
                    })

            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                # Continue with other files?
                continue

        if not all_images_with_filenames:
             raise HTTPException(status_code=400, detail="No valid images found in upload.")

        # 2. Batch Extraction
        print(f"sending {len(all_images_with_filenames)} images to LLM...")
        extracted_documents = extract_all_documents(client, all_images_with_filenames)
        
        # 3. Validation
        if not extracted_documents:
             raise HTTPException(status_code=400, detail="No valid Aadhar or PAN documents detected.")

        # 3. Validation and Merging
        def validate_and_merge(docs):
            merged_results = []
            
            # Separate by type
            aadhar_docs = [d for d in docs if d.get("Document Type") == "Aadhar"]
            pan_docs = [d for d in docs if d.get("Document Type") == "PAN"]
            dl_docs = [d for d in docs if d.get("Document Type") == "Driving Licence"]
            
            # Helper to find source image path
            def get_source_path_for_doc(doc, preferred_files=None):
                # doc["Source Files"] matches `file.filename` (e.g. "aadhar.jpg")
                # We need to find the corresponding `path` in `all_images_with_filenames`.
                # Limitation: If user uploaded "aadhar.jpg" twice, we might pick the wrong one.
                # But usually distinct filenames or we pick first match.
                
                # Optimization: Pass "preferred_files" (e.g. Aadhar Front) if we can distinguish?
                # LLM gives "Source Files": ["a.jpg", "b.jpg"].
                # We iterate `all_images_with_filenames` and return the first path that matches one of these filenames.
                
                source_filenames = doc.get("Source Files", [])
                if not source_filenames: return None

                for item in all_images_with_filenames:
                    if item["filename"] in source_filenames:
                        # Found a match. Is it the checks "Front" vs "Back"?
                        # For Aadhar, we want Front.
                        # We can't easily know which specific image path is "Front" without LLM telling us "Front came from a.jpg".
                        # Current Prompt doesn't give that mapping.
                        # Heuristic: Try to detect face in ALL source images. Return the one with biggest face?
                        return item["path"] # Just return first match for now.
                return None

            # Helper to extract face from list of possible images
            def get_face_photo(doc):
                 source_filenames = doc.get("Source Files", [])
                 best_face_path = None
                 
                 # Check all contributing images
                 candidates = [item for item in all_images_with_filenames if item["filename"] in source_filenames]
                 
                 for item in candidates:
                      face_path = extract_face(item["path"])
                      if face_path:
                           return face_path # Return first found face
                 return None

            # 3a. Validate Aadhar
            for doc in aadhar_docs:
                sides = doc.get("Sides Detected", [])
                sides = [s.title() for s in sides]
                
                has_front = "Front" in sides
                has_back = "Back" in sides
                
                if not (has_front and has_back):
                     missing = []
                     if not has_front: missing.append("Front")
                     if not has_back: missing.append("Back")
                     msg = f"Incomplete Aadhar detected ({doc.get('Name', 'Unknown')}). Missing: {', '.join(missing)}. Please upload both Front and Back sides."
                     raise HTTPException(status_code=400, detail=msg)
                
                if "Sides Detected" in doc: del doc["Sides Detected"]
                
                # Extract Photo (Aadhar Front)
                photo_path = get_face_photo(doc)
                if photo_path:
                    doc["Photo Path"] = photo_path

                merged_results.append(doc)

            # 3b. Merge PAN + DL
            if pan_docs and not dl_docs:
                 raise HTTPException(status_code=400, detail="PAN Card detected but no Driving Licence found. Please upload Driving Licence as well.")
            if dl_docs and not pan_docs:
                 raise HTTPException(status_code=400, detail="Driving Licence detected but no PAN Card found. Please upload PAN Card as well.")
            
            used_dls = set()
            
            for pan in pan_docs:
                pan_name = pan.get("Name", "").lower().strip()
                match_found = False
                
                for i, dl in enumerate(dl_docs):
                    if i in used_dls: continue
                    dl_name = dl.get("Name", "").lower().strip()
                    
                    if pan_name and dl_name and pan_name == dl_name:
                        merged_doc = pan.copy()
                        merged_doc["Document Type"] = "PAN + Driving Licence"
                        
                        if "DL Number" in dl: merged_doc["DL Number"] = dl["DL Number"]
                        if "Address" in dl: merged_doc["Address"] = dl["Address"]
                        
                        src_files = pan.get("Source Files", []) + dl.get("Source Files", [])
                        merged_doc["Source Files"] = list(set(src_files))
                        
                        # Extract Photo (Prefer PAN)
                        # Try PAN source files first
                        photo_path = get_face_photo(pan)
                        if photo_path:
                             merged_doc["Photo Path"] = photo_path
                        
                        merged_results.append(merged_doc)
                        used_dls.add(i)
                        match_found = True
                        break
                
                if not match_found:
                    # Valid mismatch (verified symmetric presence above)
                    # Extract Photo for PAN
                    photo_path = get_face_photo(pan)
                    if photo_path: pan["Photo Path"] = photo_path
                    merged_results.append(pan)

            for i, dl in enumerate(dl_docs):
                if i not in used_dls:
                    merged_results.append(dl)

            return merged_results

        final_docs = validate_and_merge(extracted_documents)
        
        if not final_docs:
             raise HTTPException(status_code=400, detail="No valid documents processed.")

        # 4. Export
        output_filename = f"extracted_{request_id}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        export_to_excel(final_docs, output_path)
        print(f"Exported to {output_path}")

        return FileResponse(
            path=output_path, 
            filename=f"extracted_data.xlsx", 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        for p in temp_files_to_cleanup:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

