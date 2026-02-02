# Project Description: Identity Document Extraction System

## 1. Executive Summary
The **Identity Document Extraction System** is an advanced AI-powered solution designed to automate the extraction of structured data from Indian identity documents, specifically **Aadhar Cards**, **PAN Cards**, and **Driving Licences**.

By leveraging state-of-the-art **Vision LLMs (Llama 3 via Groq)**, the system overcomes the limitations of traditional OCR by intelligently understanding document layouts, merging multi-sided documents (like Aadhar front and back) into a single identity, and extracting user photographs.

## 2. Core Capabilities

### 2.1 Multi-Document Intelligence
The system is built to handle the complexity of real-world documents:
-   **Aadhar Cards**: Automatically detects Front and Back sides. If both are present for the same person, they are **merged** into a single, complete record containing Name, Address, DOB, Gender, and Aadhar Number.
-   **PAN Cards**: Extracts Name, Father's Name, DOB, and PAN Number.
-   **Driving Licences**: Extracts Name, DL Number, and Address.

### 2.2 Identity Merging Engine
A key differentiator is the logic in `main.py` that post-processes LLM results. It intelligently groups documents based on:
1.  **ID Numbers**: Matching Aadhar or PAN numbers.
2.  **Name Matching**: Fuzzy matching on names to group documents belonging to the same individual.

### 2.3 Face Extraction
The system includes a dedicated `face_extractor.py` module using OpenCV. It:
-   Scans the document for faces.
-   Crops and saves the best candidate face.
-   Returns both a hosted URL and a Base64 string for easy UI integration.

## 3. Technical Architecture

### 3.1 Stack
-   **Backend Framework**: **FastAPI** (Python) for high-performance, async API handling.
-   **AI Inference**: **Groq API** running **Llama 3 Vision**. Groq's LPU (Language Processing Unit) ensures ultra-low latency.
-   **Image Processing**: **Pillow (PIL)** for image manipulation and **OpenCV** for face detection.
-   **Containerization**: **Docker** support for one-click deployment.

### 3.2 Data Flow Workflow
1.  **Input**: User uploads multiple files (PDFs, JPGs) via the API or Frontend.
2.  **Preprocessing**:
    -   PDFs are converted to high-res images (`pdf_processor.py`).
    -   Images are validated and stored temporarily.
3.  **AI Analysis**:
    -   All images are batched and sent to the **Groq API** with a complex prompt (`llm_extractor.py`).
    -   The prompt instructs the Llama 3 model to classify documents and extract specific fields in JSON format.
4.  **Post-Processing & Merging**:
    -   Raw JSON from the LLM is processed.
    -   The **Identity Merging Logic** combines related documents.
    -   **Face Extraction** is triggered for each unique identity.
5.  **Output**: A standardized JSON response containing extracted text, photo URLs, and Base64 images is returned to the client.

## 4. API Specification

**Endpoint**: `POST /extract/`

**Request Body** (`multipart/form-data`):
-   `files`: Array of files.

**Response Structure**:
```json
{
  "status": "success",
  "request_id": "uuid...",
  "data": [
    {
      "Document Type": "Aadhar",
      "Name": "John Doe",
      "Aadhar Number": "xxxx-xxxx-xxxx",
      "Photo URL": "/static/faces/...",
      ...
    }
  ]
}
```

## 5. Deployment
The project is designed for cloud deployment (e.g., Render.com).
-   **Dockerfile**: Included for building a lightweight Python environment.
-   **Environment Variables**: `GROQ_API_KEY` is the only external dependency.

## 6. Future Roadmap
-   **Excel Export**: Re-enable the feature to download data as `.xlsx`.
-   **Database Integration**: Persist extracted identities for long-term storage.
-   **Authentication**: Add API key or OAuth for user security.
