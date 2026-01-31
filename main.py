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
    
    try:
        if not client:
             raise HTTPException(status_code=500, detail="LLM Client not initialized. Check server logs/API Key.")

        for file in files:
            # Basic validation
            if not file.filename.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
                continue

            temp_path = os.path.join(TEMP_DIR, f"{request_id}_{file.filename}")
            
            try:
                # Save uploaded file
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Convert to Images
                images = []
                if file.filename.lower().endswith(".pdf"):
                    images = convert_pdf_to_images(temp_path)
                else:
                    from PIL import Image
                    try:
                        img = Image.open(temp_path).convert('RGB')
                        images = [img]
                    except Exception as e:
                        print(f"Image load failed for {file.filename}: {e}")
                        continue
                
                # Add to collection
                for img in images:
                    all_images_with_filenames.append({
                        "image": img,
                        "filename": file.filename
                    })

            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

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
            
            # 3a. Validate Aadhar
            for doc in aadhar_docs:
                sides = doc.get("Sides Detected", [])
                # Normalize case just in case
                sides = [s.title() for s in sides]
                
                # Check for completeness
                has_front = "Front" in sides
                has_back = "Back" in sides
                
                if not (has_front and has_back):
                     # STRICT VALIDATION RULE
                     missing = []
                     if not has_front: missing.append("Front")
                     if not has_back: missing.append("Back")
                     msg = f"Incomplete Aadhar detected ({doc.get('Name', 'Unknown')}). Missing: {', '.join(missing)}. Please upload both Front and Back sides."
                     raise HTTPException(status_code=400, detail=msg)
                
                # If valid, just add to results (clean up internal field)
                if "Sides Detected" in doc:
                    del doc["Sides Detected"]
                merged_results.append(doc)

            # 3b. Merge PAN + DL
            # Validate Presence (Symmetric)
            if pan_docs and not dl_docs:
                 raise HTTPException(status_code=400, detail="PAN Card detected but no Driving Licence found. Please upload Driving Licence as well.")
            if dl_docs and not pan_docs:
                 raise HTTPException(status_code=400, detail="Driving Licence detected but no PAN Card found. Please upload PAN Card as well.")

            # Logic: For each PAN, look for matching DL (Name + maybe DOB).
            # If match -> Merge. If no match -> Keep separate.
            # Also handle DLs that don't match any PAN.
            
            used_dls = set()
            
            for pan in pan_docs:
                pan_name = pan.get("Name", "").lower().strip()
                match_found = False
                
                for i, dl in enumerate(dl_docs):
                    if i in used_dls: continue
                    
                    dl_name = dl.get("Name", "").lower().strip()
                    
                    # Basic Name Match
                    if pan_name and dl_name and pan_name == dl_name:
                        # MERGE
                        merged_doc = pan.copy()
                        merged_doc["Document Type"] = "PAN + Driving Licence"
                        
                        # Add DL unique fields
                        if "DL Number" in dl: merged_doc["DL Number"] = dl["DL Number"]
                        if "Address" in dl: merged_doc["Address"] = dl["Address"] # Prefer DL address or keep PAN? Prompt says Addr from DL.
                        
                        # Add source files
                        src_files = pan.get("Source Files", []) + dl.get("Source Files", [])
                        merged_doc["Source Files"] = list(set(src_files))
                        
                        merged_results.append(merged_doc)
                        used_dls.add(i)
                        match_found = True
                        break
                
                if not match_found:
                    # PAN exists but no matching DL found (Name mismatch).
                    # Since we verified dl_docs exists at the top, this means valid mismatch.
                    merged_results.append(pan)

            # Add remaining unmatched DLs
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

