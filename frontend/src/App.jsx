import { useState } from 'react'
import axios from 'axios'
import { Logo } from './components/Logo'

function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [searchText, setSearchText] = useState('')
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pdfUrl, setPdfUrl] = useState(null)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
      setPdfUrl(URL.createObjectURL(file))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a PDF file');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('text', searchText);

    try {
      console.log('Sending request to backend...');
      const response = await axios.post('/api', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000,
      });

      console.log('Response from backend:', response.data);
      
      if (!response.data) {
        throw new Error('No response data received');
      }

      if (response.data.error) {
        setError(response.data.error);
        return;
      }

      if (!Array.isArray(response.data.results)) {
        throw new Error('Invalid response format: results should be an array');
      }

      setResults(response.data.results);
      
      if (response.data.results.length === 0) {
        setError('No matching references found in the document');
      }
    } catch (err) {
      console.error('Error processing PDF:', err);
      setResults(null);
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else if (err.code === 'ECONNABORTED') {
        setError('Request timed out. The file might be too large or the server is busy.');
      } else if (!navigator.onLine) {
        setError('You appear to be offline. Please check your internet connection.');
      } else {
        setError(err.message || 'An error occurred while processing your request');
      }
    } finally {
      setLoading(false);
    }
  }

  const openPdfWithHighlight = (quote) => {
    if (!results?.filename) return;
    
    const pdfViewerUrl = `https://mozilla.github.io/pdf.js/web/viewer.html`
    const pdfUrl = `/api/pdf/${results.filename}`
    
    // Open PDF viewer
    const win = window.open(`${pdfViewerUrl}?file=${encodeURIComponent(pdfUrl)}#page=${quote.page}`, '_blank')
    
    // Wait for PDF to load then use PDFViewerApplication's find
    setTimeout(() => {
      if (win) {
        const script = `
          if (window.PDFViewerApplication && PDFViewerApplication.initialized) {
            const searchText = ${JSON.stringify(quote.quote.trim().replace(/\s+/g, ' '))};
            
            // Configure find controller for exact matches
            PDFViewerApplication.findController.executeCommand('find', {
              query: searchText,
              phraseSearch: true,
              highlightAll: true,
              caseSensitive: true,
              entireWord: true,
              findPrevious: false
            });
          }
        `;
        win.eval(script);
      }
    }, 2000); // Give it more time to load
  }

  return (
    <div className="h-full flex flex-col">
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

      <main className="flex-1 flex flex-col bg-white">
        <div className="container-center">
          <div className="flex flex-col items-center w-full max-w-3xl mx-auto pt-12 pb-16">
            <div className="w-full space-y-12">
              <div>
                <div className="text-center mb-8">
                  <h1 className="font-display text-5xl font-bold tracking-tight text-neutral-900 sm:text-6xl lg:text-7xl">
                    Find Perfect Citations
                    <span className="text-primary-600">.</span>
                  </h1>
                  <p className="mt-6 text-xl leading-8 text-neutral-600">
                    Upload your PDF, paste your text, and get instant Harvard-style citations
                    with perfect formatting and page numbers.
                  </p>
                </div>

                <div className="card p-8 w-full mt-8 border-2 border-black rounded-xl">
                  <form onSubmit={handleSubmit} className="space-y-8">
                    <div>
                      <label className="block text-lg font-bold text-neutral-800 mb-3">
                        Upload Academic Paper (PDF)
                      </label>
                      <div className="mt-2 flex justify-center px-8 pt-6 pb-8 border-2 border-black rounded-xl hover:border-primary-500 transition-colors cursor-pointer bg-neutral-50 hover:bg-white">
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
                      disabled={loading || !selectedFile || !searchText.trim()}
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
                        {loading ? 'Processing...' : 'Find References'}
                      </span>
                      <span className="relative invisible">
                        {loading ? 'Processing...' : 'Find References'}
                      </span>
                    </button>
                  </form>
                </div>
              </div>
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 p-4 mb-6 mt-8 border-2 border-black">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {results && (
              <div className="w-full mt-8">
                <div className="card p-6 border-2 border-black">
                  <h2 className="text-xl font-semibold text-neutral-900 mb-4">
                    Found References
                  </h2>
                  {results.quotes.length > 0 ? (
                    <div className="space-y-6 bg-white">
                      {results.quotes.map((quote, index) => {
                        let highlightedQuote = quote.quote;
                        quote.highlighted_terms.forEach(term => {
                          const regex = new RegExp(`(${term})`, 'gi');
                          highlightedQuote = highlightedQuote.replace(
                            regex,
                            '<mark class="bg-yellow-200">$1</mark>'
                          );
                        });

                        return (
                          <div
                            key={index}
                            className="card card-hover p-6 transition-all duration-200 border-2 border-black"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1">
                                <p 
                                  className="text-neutral-700 text-lg leading-relaxed"
                                  dangerouslySetInnerHTML={{ __html: highlightedQuote }}
                                />
                                <div className="mt-4 flex items-center gap-4">
                                  <span className="text-sm text-neutral-500">
                                    Page {quote.page}
                                  </span>
                                  <span className="text-sm font-medium text-neutral-900">
                                    {quote.citation}
                                  </span>
                                  <button
                                    onClick={() => openPdfWithHighlight(quote)}
                                    className="btn btn-secondary text-sm"
                                  >
                                    View in PDF
                                  </button>
                                </div>
                              </div>
                              <button
                                onClick={() => {
                                  navigator.clipboard.writeText(quote.citation);
                                }}
                                className="btn btn-secondary shrink-0"
                                title="Copy citation"
                              >
                                <svg
                                  className="h-4 w-4"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
                                  />
                                </svg>
                                <span className="ml-2">Copy</span>
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-neutral-600">
                      {results.message || "No matching quotes found"}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-black bg-white mt-auto">
        <div className="container-center">
          <div className="flex h-16 items-center justify-between">
            <p className="text-sm text-neutral-500">
              2025 CiteSmart. All rights reserved.
            </p>
            <div className="flex space-x-6">
              <a
                href="#"
                className="text-neutral-400 hover:text-neutral-500"
              >
                Privacy
              </a>
              <a
                href="#"
                className="text-neutral-400 hover:text-neutral-500"
              >
                Terms
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
