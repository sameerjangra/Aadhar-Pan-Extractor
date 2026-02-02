# Identity Document Extraction System

A high-performance, AI-powered tool designed to extract structured data from Indian identity documents (Aadhar Card, PAN Card, Driving Licence). Built with **FastAPI** and **Llama 3 (via Groq)**, it features intelligent identity merging and face extraction.

## 🚀 Key Features

-   **Multi-Document Support**: Seamlessly processes **Aadhar Cards**, **PAN Cards**, and **Driving Licences**.
-   **Intelligent Identity Merging**: Automatically detects and merges separate files (e.g., Aadhar Front & Back) belonging to the same individual into a single, unified record.
-   **Face Extraction**: Detects and extracts user photos from ID cards, determining the best candidate image.
-   **High Precision OCR**: Utilizes **Llama 3 Vision** capabilities (via Groq) for accurate text extraction, even from complex or noisy images.
-   **Format Flexibility**: Accepts PDF, JPG, JPEG, and PNG files.
-   **JSON API**: Returns a clean, standardized JSON response for easy integration.
-   **Docker Ready**: tailored for easy deployment on platforms like Render.

## 🛠️ Technology Stack

-   **Backend**: Python, FastAPI
-   **AI/LLM**: Groq API (Llama 3)
-   **Image Processing**: Pillow (PIL)
-   **Containerization**: Docker

## 📝 API Usage

### Endpoint
`POST /extract/`

### Request
-   **Method**: `POST`
-   **Content-Type**: `multipart/form-data`
-   **Body**:
    -   `files`: List of files (images or PDFs) to process.

### Example (cURL)
```bash
curl -X POST "http://localhost:8000/extract/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@/path/to/aadhar_front.jpg" \
  -F "files=@/path/to/aadhar_back.jpg"
```

### Response Example
```json
{
  "status": "success",
  "request_id": "c4d5e6f7-...",
  "data": [
    {
      "Document Type": "Aadhar",
      "Name": "Ravi Kumar",
      "Aadhar Number": "1234 5678 9012",
      "Gender": "Male",
      "Date of Birth": "1990-01-01",
      "Address": "123, Main Street, New Delhi...",
      "Photo URL": "/static/faces/abc-123.jpg",
      "Photo Base64": "data:image/jpeg;base64,..."
    }
  ]
}
```

## ⚙️ Setup & Installation

### Prerequisites
-   Python 3.9+
-   [Groq API Key](https://console.groq.com/)

### Local Development

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd <repo-name>
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```env
    GROQ_API_KEY=gsk_your_actual_key_here
    ```

4.  **Run the Server**:
    ```bash
    uvicorn main:app --reload
    ```

5.  **Access the App**:
    -   API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
    -   Demo UI: [http://localhost:8000](http://localhost:8000)

## 🐳 Docker Deployment

1.  **Build the Image**:
    ```bash
    docker build -t identity-extractor .
    ```

2.  **Run the Container**:
    ```bash
    docker run -p 8000:8000 --env-file .env identity-extractor
    ```

## 📂 Project Structure

```
├── main.py             # FastAPI application entry point
├── llm_extractor.py    # LLM interaction logic (Groq)
├── face_extractor.py   # Face detection and cropping
├── pdf_processor.py    # PDF to image conversion
├── static/             # Static assets and extracted faces
├── templates/          # HTML templates (if any)
├── requirements.txt    # Python dependencies
└── Dockerfile          # Docker configuration
```

## 📄 License
MIT License
