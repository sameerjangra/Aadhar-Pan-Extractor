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

        # Validation Logic
        merged_results = []
        
        aadhar_docs = [d for d in extracted_documents if d.get("Document Type") == "Aadhar"]
        pan_docs = [d for d in extracted_documents if d.get("Document Type") == "PAN"]
        dl_docs = [d for d in extracted_documents if d.get("Document Type") == "Driving Licence"]
        
        # Validate Aadhar
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
            
            # Extract Photo
            photo_path = get_face_photo(doc)
            if photo_path: doc["Photo Path"] = photo_path

            merged_results.append(doc)

        # Validate PAN/DL
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
                    photo_path = get_face_photo(pan)
                    if photo_path: merged_doc["Photo Path"] = photo_path
                    
                    merged_results.append(merged_doc)
                    used_dls.add(i)
                    match_found = True
                    break
            
            if not match_found:
                photo_path = get_face_photo(pan)
                if photo_path: pan["Photo Path"] = photo_path
                merged_results.append(pan)

        for i, dl in enumerate(dl_docs):
            if i not in used_dls:
                merged_results.append(dl)

        if not merged_results:
             raise HTTPException(status_code=400, detail="No valid documents processed.")
        
        return request_id, merged_results

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
