import { useState } from 'react'
import axios from 'axios'
import { Logo } from './components/Logo'

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [results, setResults] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setMetadata(null);
      setResults([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResults([]);
    setMetadata(null);

    if (!selectedFile) {
      setError('Please select a PDF file');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('text', searchText);

    try {
      const response = await axios.post('http://localhost:5003/api', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      if (response.data.error) {
        setError(response.data.error);
        return;
      }

      setPdfUrl(response.data.pdf_url);
      setResults(response.data.results || []);
      setMetadata(response.data.metadata || null);
      
    } catch (err) {
      setError(err.message || 'Error processing PDF');
    }
  };

  const openPdfViewer = () => {
    if (!pdfUrl) return;
    const viewerUrl = `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(pdfUrl)}`;
    window.open(viewerUrl, '_blank');
  };

  return (
    <div className="min-h-screen bg-white">
      <nav className="border-b border-black bg-white">
        <div className="container-center">
          <div className="flex h-16 items-center justify-between">
            <Logo />
            <a
              href="https://github.com/yourusername/citesmart"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-neutral-500 hover:text-neutral-900"
            >
              <svg
                className="h-6 w-6"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  fillRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  clipRule="evenodd"
                />
              </svg>
              GitHub
            </a>
          </div>
        </div>
      </nav>

      <main className="relative">
        <div className="px-6 pt-14 lg:px-8">
          <div className="mx-auto max-w-4xl py-8">
            {error && (
              <div className="mb-8">
                <div className="rounded-xl bg-red-50 p-4 border-2 border-black">
                  <div className="flex">
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">Error</h3>
                      <div className="mt-2 text-sm text-red-700">
                        <p>{error}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div>
              <div className="text-center mb-8">
                <h1 className="font-display text-5xl font-bold tracking-tight text-neutral-900 sm:text-6xl lg:text-7xl">
                  Find Perfect
                  <br />
                  Citations
                  <span className="text-primary-600">.</span>
                </h1>
                <p className="mt-6 text-xl leading-8 text-neutral-600 max-w-3xl mx-auto">
                  Upload your PDF, paste your text, and get instant Harvard-style citations with perfect formatting and page numbers.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-lg font-bold text-neutral-800 mb-3">
                    Upload Academic Paper (PDF)
                  </label>
                  <div className="mt-2 flex justify-center px-8 pt-6 pb-8 border-2 border-black rounded-xl hover:border-primary-500 transition-colors cursor-pointer bg-white">
                    <div className="space-y-2 text-center">
                      <svg
                        className="mx-auto h-16 w-16 text-neutral-400 group-hover:text-primary-500"
                        stroke="currentColor"
                        fill="none"
                        viewBox="0 0 48 48"
                        aria-hidden="true"
                      >
                        <path
                          d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      <div className="flex text-base text-neutral-600 justify-center">
                        <label
                          htmlFor="file-upload"
                          className="relative cursor-pointer rounded-md font-bold text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                        >
                          <span>Upload a file</span>
                          <input
                            id="file-upload"
                            name="file-upload"
                            type="file"
                            accept=".pdf"
                            className="sr-only"
                            onChange={handleFileChange}
                          />
                        </label>
                        <p className="pl-1 font-medium">or drag and drop</p>
                      </div>
                      <p className="text-sm text-neutral-500 font-medium">PDF up to 10MB</p>
                      {selectedFile && (
                        <div className="mt-4 py-2 px-4 bg-primary-50 rounded-lg border border-black">
                          <p className="text-base text-primary-700 font-bold">
                            Selected: {selectedFile.name}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-lg font-bold text-neutral-800 mb-3">
                    Your Text
                  </label>
                  <textarea
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    rows="4"
                    className="w-full px-4 py-3 text-base font-medium border-2 border-black rounded-xl focus:border-primary-500 focus:ring-primary-500 placeholder-neutral-400"
                    placeholder="Paste your text here to find relevant quotes..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={!selectedFile || !searchText.trim()}
                  className="relative w-full inline-flex items-center justify-center px-8 py-4 overflow-hidden text-lg font-bold text-white transition duration-300 ease-out bg-primary-600 border-2 border-black rounded-xl shadow-lg hover:bg-primary-700 active:bg-primary-800 disabled:bg-primary-600 group"
                >
                  <span className="absolute inset-0 flex items-center justify-center w-full h-full text-white duration-300 -translate-x-full bg-primary-700 group-hover:translate-x-0 ease">
                    <svg 
                      className="w-8 h-8" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth="2" 
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                  </span>
                  <span className="absolute flex items-center justify-center w-full h-full text-white transition-all duration-300 transform group-hover:translate-x-full ease">
                    Find References
                  </span>
                  <span className="relative invisible">
                    Find References
                  </span>
                </button>
              </form>

              {metadata && (
                <div className="mt-8">
                  <div className="rounded-xl border-2 border-black p-6 bg-white">
                    <h2 className="text-xl font-bold mb-4">Document Information</h2>
                    <div className="space-y-2">
                      <p><span className="font-semibold">Title:</span> {metadata.title}</p>
                      <p>
                        <span className="font-semibold">Authors:</span>{' '}
                        {metadata.authors.length > 0
                          ? metadata.authors.join(', ')
                          : 'Unknown'
                        }
                      </p>
                      <p><span className="font-semibold">Published:</span> {metadata.published_date}</p>
                      <p><span className="font-semibold">DOI:</span> {metadata.doi}</p>
                      <p><span className="font-semibold">Journal:</span> {metadata.journal}</p>
                      <p><span className="font-semibold">Publisher:</span> {metadata.publisher}</p>
                      <p><span className="font-semibold">Type:</span> {metadata.type}</p>
                    </div>
                  </div>
                </div>
              )}

              {results.length > 0 && (
                <div className="mt-8">
                  <div className="rounded-xl border-2 border-black p-6">
                    <h2 className="text-xl font-bold mb-4">Found References</h2>
                    <div className="space-y-4">
                      {results.map((result, index) => (
                        <div key={index} className="p-4 border-2 border-black rounded-xl">
                          <div className="flex items-center justify-between mb-2">
                            <p className="text-sm text-neutral-500">Page {result.page}</p>
                            <button
                              onClick={openPdfViewer}
                              className="px-4 py-2 text-sm font-semibold text-primary-600 border-2 border-primary-600 rounded-lg hover:bg-primary-50"
                            >
                              Open in PDF Viewer
                            </button>
                          </div>
                          <p 
                            className="text-lg mt-2"
                            dangerouslySetInnerHTML={{ __html: result.text }}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App
