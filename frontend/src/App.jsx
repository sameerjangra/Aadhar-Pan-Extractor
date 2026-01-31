import { useState } from 'react'
import axios from 'axios'

function App() {
    const [files, setFiles] = useState([])
    const [loading, setLoading] = useState(false)
    const [downloadUrl, setDownloadUrl] = useState(null)
    const [error, setError] = useState(null)
    const [status, setStatus] = useState("")

    const handleFileChange = (e) => {
        setFiles(Array.from(e.target.files))
        setDownloadUrl(null)
        setError(null)
        setStatus("")
    }

    const handleUpload = async () => {
        if (files.length === 0) return

        setLoading(true)
        setError(null)
        setStatus(`Uploading and Processing ${files.length} files...`)

        const formData = new FormData()
        files.forEach((file) => {
            formData.append('files', file)
        })

        try {
            const response = await axios.post('/extract/', formData, {
                responseType: 'blob',
            })

            const url = window.URL.createObjectURL(new Blob([response.data]))
            setDownloadUrl(url)
            setStatus("Extraction Complete!")
        } catch (err) {
            console.error(err)
            setError("An error occurred. Ensure all files are valid PDFs/Images.")
            setStatus("Failed.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="app-container">
            <div className="glass-card">
                <header>
                    <h1>Aadhar Pan Extraction</h1>
                    <p className="subtitle">Upload Aadhar and PAN cards to get structured data.</p>
                </header>

                <div className="upload-section">
                    <input
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        multiple
                        onChange={handleFileChange}
                        id="file-upload"
                        className="file-input"
                    />
                    <label htmlFor="file-upload" className="file-label">
                        {files.length > 0 ? `${files.length} files selected` : "Choose Files"}
                    </label>
                </div>

                {files.length > 0 && (
                    <div className="file-list">
                        <ul>
                            {files.map((f, i) => (
                                <li key={i}>{f.name}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {error && <div className="error-message">{error}</div>}

                <button
                    onClick={handleUpload}
                    disabled={files.length === 0 || loading}
                    className={`primary-button ${loading ? 'loading' : ''}`}
                >
                    {loading ? "Processing..." : "Extract Data"}
                </button>

                {status && <p className="status-text">{status}</p>}

                {downloadUrl && (
                    <div className="result-section">
                        <a href={downloadUrl} download="extracted_data.xlsx" className="download-button">
                            Download Excel Report
                        </a>
                    </div>
                )}
            </div>
        </div>
    )
}

export default App
