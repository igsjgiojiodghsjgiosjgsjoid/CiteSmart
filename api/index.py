from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
import PyPDF2
import io
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import traceback
import os
import sys
import logging
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(pdf_file):
    try:
        logger.info("Starting PDF extraction")
        
        # Create a BytesIO object from the uploaded file
        pdf_bytes = io.BytesIO(pdf_file.read())
        
        # Create PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_bytes)
        logger.info(f"Successfully created PDF reader. Pages: {len(pdf_reader.pages)}")
        
        # Extract text and look for DOIs from all pages
        text = ""
        dois = set()
        
        for page_num in range(len(pdf_reader.pages)):
            try:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
                
                # Extract DOIs from the page text
                page_dois = extract_doi(page_text)
                dois.update(page_dois)
                
                # Get any URLs from the page's annotations/links
                if '/Annots' in page:
                    annotations = page['/Annots']
                    for annotation in annotations:
                        if isinstance(annotation, PyPDF2.generic.IndirectObject):
                            annotation = annotation.get_object()
                        if annotation.get('/Subtype') == '/Link' and '/A' in annotation:
                            if '/URI' in annotation['/A']:
                                url = annotation['/A']['/URI']
                                # Check if the URL contains a DOI
                                url_dois = extract_doi(url)
                                dois.update(url_dois)
                
                logger.info(f"Extracted text and DOIs from page {page_num + 1}")
            except Exception as e:
                logger.error(f"Error extracting from page {page_num + 1}: {str(e)}")
                continue
        
        if not text.strip():
            raise Exception("No text could be extracted from the PDF")
        
        return text, list(dois)
    except Exception as e:
        logger.error(f"Error in extract_text_from_pdf: {str(e)}")
        raise

def extract_doi(text):
    """Extract DOI from text using various patterns including URLs."""
    # Standard DOI pattern
    doi_patterns = [
        r'\b(10\.\d{4,}/[-._;()/:\w]+)\b',  # Standard DOI pattern
        r'https?://doi\.org/(10\.\d{4,}/[-._;()/:\w]+)',  # DOI URL pattern
        r'https?://dx\.doi\.org/(10\.\d{4,}/[-._;()/:\w]+)'  # dx.doi.org pattern
    ]
    
    dois = set()
    for pattern in doi_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Extract just the DOI part if it's a URL
            doi = match.group(1) if 'doi.org' in pattern else match.group(0)
            # Clean up the DOI
            doi = doi.strip().rstrip('.')
            dois.add(doi)
    
    return list(dois)

def process_text(text, search_query):
    try:
        # Split text into sentences
        sentences = sent_tokenize(text)
        logger.info(f"Split text into {len(sentences)} sentences")
        
        # Convert search query to lowercase for comparison
        search_query = search_query.lower()
        search_words = set(word_tokenize(search_query))
        
        # Try to extract author information from the text
        author_match = re.search(r'by\s+([^,\.]+)', text)
        author = author_match.group(1) if author_match else "Unknown Author"
        
        # Try to extract year
        year_match = re.search(r'\((\d{4})\)', text)
        year = year_match.group(1) if year_match else ""
        
        results = []
        for i, sentence in enumerate(sentences):
            # Convert sentence to lowercase and tokenize
            sentence_lower = sentence.lower()
            sentence_words = set(word_tokenize(sentence_lower))
            
            # Calculate simple word overlap
            common_words = search_words.intersection(sentence_words)
            if common_words:
                similarity = len(common_words) / len(search_words)
                if similarity > 0.3:  # Adjust threshold as needed
                    # Create Harvard style citation
                    citation = f"{author} ({year})" if year else author
                    
                    results.append({
                        'text': sentence,
                        'similarity': float(similarity),
                        'page': 1,  # Default to page 1 since we can't extract page numbers yet
                        'citation': citation,
                        'highlighted_terms': list(common_words)
                    })
        
        # Sort results by similarity score
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
    except Exception as e:
        logger.error(f"Error in process_text: {str(e)}")
        raise

@app.route('/api', methods=['POST', 'OPTIONS'])
def handle_request():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        logger.info("Received POST request")
        
        # Check if file is present
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if not file or not file.filename:
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        if not file.filename.lower().endswith('.pdf'):
            logger.error("Invalid file type")
            return jsonify({'error': 'Please upload a PDF file'}), 400
        
        # Get search text
        search_text = request.form.get('text', '').strip()
        if not search_text:
            logger.error("No search text provided")
            return jsonify({'error': 'Please provide search text'}), 400
        
        logger.info(f"Processing file: {file.filename}")
        logger.info(f"Search text: {search_text}")
        
        # Extract text from PDF
        try:
            pdf_text, dois = extract_text_from_pdf(file)
            logger.info("Successfully extracted text and DOIs from PDF")
            logger.info(f"Found DOIs: {dois}")
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            return jsonify({'error': 'Could not read the PDF file. Please make sure it\'s a valid PDF.'}), 400
        
        # Process text and find matches
        try:
            results = process_text(pdf_text, search_text)
            # Add DOIs to the response
            response_data = {
                'results': results,
                'dois': dois
            }
            logger.info(f"Found {len(results)} matches and {len(dois)} DOIs")
            return jsonify(response_data)
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            return jsonify({'error': 'Error processing text'}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/pdf/<filename>', methods=['GET'])
def serve_pdf(filename):
    try:
        # Get the file from the request
        if not hasattr(request, 'files') or 'file' not in request.files:
            return jsonify({'error': 'No file found'}), 400
            
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'Invalid file'}), 400
            
        # Create a BytesIO object from the file
        file_data = io.BytesIO(file.read())
        file_data.seek(0)
        
        # Send the file
        return send_file(
            file_data,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error serving PDF: {str(e)}")
        return jsonify({'error': 'Could not serve PDF file'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
