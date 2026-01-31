# Aadhar & PAN Card Extraction

A specialized tool to extract data from Aadhar and PAN cards.

## Features
- **Multi-file Upload**: Supports PDF, JPG, JPEG, PNG.
- **Auto-Classification**: Detects Aadhar vs PAN.
- **JSON API**: Standardized JSON output for integration.
- **Photo Extraction**: Extracts user photos and returns accessible URLs.

## 🚀 API Usage

### **Endpoint**
`POST /extract/`

### **Request**
- **Method**: `POST`
- **Body**: `multipart/form-data`
- **Key**: `files` (Upload 1 or more PDF/Image files)

### **Response (JSON)**
```json
{
  "status": "success",
  "request_id": "uuid-string",
  "data": [
    {
      "Document Type": "Aadhar",
      "Name": "John Doe",
      "Aadhar Number": "1234 5678 9012",
      "Photo URL": "/static/faces/abc-123.jpg",
      ...
    }
  ]
}
```

### **Example (cURL)**
```bash
curl -X POST "https://your-app-url.onrender.com/extract/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@/path/to/aadhar.jpg"
```

## Usage

### Option 1: Quick Start (Recommended)
This runs the backend with a built-in static frontend. No Node.js required.

1.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the server**:
    ```bash
    uvicorn main:app --reload
    ```
3.  **Open the App**:
    - Go to [http://localhost:8000](http://localhost:8000)

### Option 2: React Frontend (Advanced)
Use this only if you want to develop the React frontend. Requires Node.js.

1.  Navigate to `frontend/`:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
    The app will be available at imports `http://localhost:5173`.

## How to Use
1.  Open the frontend URL (e.g., `http://localhost:8000`).
2.  Upload a scanned policy PDF or Image.
3.  Click **Extract**.
4.  Wait for the extraction to complete (OCR + LLM can take 30-60 seconds).
5.  Download the generated Excel report.

