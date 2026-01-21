# Insurance Policy Extractor

## Prerequisites
1. **Python 3.10+** (Already in environment)
2. **Tesseract OCR** (Must be installed on the system and in PATH)
3. **OpenAI API Key** (Set as environment variable `OPENAI_API_KEY`)
4. **Node.js 18+** (Required for Frontend)

## Setup & Run

### Backend
1. Navigate to `insurance_extraction_app`:
   ```bash
   cd insurance_extraction_app
   ```
2. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

### Frontend
1. Navigate to `insurance_extraction_app/frontend`:
   ```bash
   cd frontend
   ```
2. Install dependencies (requires Node.js):
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:5173`.

## Usage
1. Open the frontend URL.
2. Upload a scanned policy PDF.
3. Wait for the extraction to complete (OCR + LLM can take 30-60 seconds).
4. Download the generated Excel report.
