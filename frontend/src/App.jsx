import { useState } from 'react'
import axios from 'axios'

function App() {
    const [file, setFile] = useState(null)
    const [loading, setLoading] = useState(false)
    const [downloadUrl, setDownloadUrl] = useState(null)
    const [error, setError] = useState(null)
    const [status, setStatus] = useState("")

    const handleFileChange = (e) => {
        setFile(e.target.files[0])
        setDownloadUrl(null)
        setError(null)
        setStatus("")
    }

    const handleUpload = async () => {
        if (!file) return

        setLoading(true)
        setError(null)
        setStatus("Uploading and Processing... This may take a minute.")

        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await axios.post('http://localhost:8000/extract/', formData, {
                responseType: 'blob', // Important for file download
            })

            // Create blob link to download
            const url = window.URL.createObjectURL(new Blob([response.data]))
            setDownloadUrl(url)
            setStatus("Extraction Complete!")
        } catch (err) {
            console.error(err)
            setError("An error occurred during extraction. Please try again.")
            setStatus("Failed.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="app-container">
            <div className="glass-card">
                <header>
                    <h1>Insurance Policy AI Extractor</h1>
                    <p className="subtitle">Upload your scanned policy PDF and get structured data instantly.</p>
                </header>

                <div className="upload-section">
                    <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileChange}
                        id="file-upload"
                        className="file-input"
                    />
                    <label htmlFor="file-upload" className="file-label">
                        {file ? file.name : "Choose PDF File"}
                    </label>
                </div>

                {error && <div className="error-message">{error}</div>}

                <button
                    onClick={handleUpload}
                    disabled={!file || loading}
                    className={`primary-button ${loading ? 'loading' : ''}`}
                >
                    {loading ? "Processing..." : "Extract Data"}
                </button>

                {status && <p className="status-text">{status}</p>}

                {downloadUrl && (
                    <div className="result-section">
                        <a href={downloadUrl} download={`extracted_${file?.name}.xlsx`} className="download-button">
                            Download Excel Report
                        </a>
                    </div>
                )}
            </div>
        </div>
    )
}

export default App
