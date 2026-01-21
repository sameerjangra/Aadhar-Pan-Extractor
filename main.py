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
from ocr_engine import extract_text_from_images
from text_cleaner import clean_ocr_text
from llm_extractor import extract_data_with_llm
from data_exporter import export_to_excel

app = FastAPI(title="Insurance Policy Extractor")

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",
    "http://localhost:8000",
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

@app.post("/extract/")
async def extract_policy_data(file: UploadFile = File(...)):
    """
    Upload a PDF policy file, extract data, and return an Excel file.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    request_id = str(uuid.uuid4())
    temp_pdf_path = os.path.join(TEMP_DIR, f"{request_id}_{file.filename}")
    
    try:
        # Save uploaded file
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Processing file: {temp_pdf_path}")

        # 1. Convert PDF to Images
        images = convert_pdf_to_images(temp_pdf_path)
        print(f"Converted to {len(images)} images.")

        if not images:
            raise HTTPException(status_code=400, detail="Failed to convert PDF to images.")

        # 2. LLM Extraction (Vision) - Skipping OCR/Cleaning
        print("Sending images to LLM (Vision)...")
        extracted_data = extract_data_with_llm(images)
        print(f"LLM Extraction complete: {extracted_data}")

        # 3. Export to Excel
        output_filename = f"extracted_{request_id}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        export_to_excel(extracted_data, output_path)
        print(f"Exported to {output_path}")

        # Return the file
        # We use FileResponse. It is often good practice to clean up, but for debugging we might keep files.
        # For this demo, let's keep them.
        return FileResponse(
            path=output_path, 
            filename=f"extracted_{file.filename}.xlsx", 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Optional: cleanup temp pdf
        # if os.path.exists(temp_pdf_path):
        #     os.remove(temp_pdf_path)
        pass
