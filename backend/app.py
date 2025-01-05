from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PyPDF2 import PdfReader
from nltk.tokenize import sent_tokenize
import re
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import json
import requests

app = Flask(__name__, static_folder='pdfs')
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdfs')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_text_from_pdf(file):
    """Extract text from PDF file."""
    text_by_page = {}
    try:
        pdf_reader = PdfReader(file)
        for i, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            if text.strip():  # Only store pages with text
                text_by_page[i] = text.strip()
        return text_by_page
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        return {}

def extract_doi_from_text(text):
    """Extract DOI from text using regex patterns."""
    # Common DOI patterns
    doi_patterns = [
        r'doi\.org/([^\s]+)',
        r'DOI:\s*([^\s]+)',
        r'doi:([^\s]+)',
        r'(?:https?://)?(?:dx\.)?doi\.org/(.+)',
    ]
    
    for pattern in doi_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            doi = match.group(1).strip()
            # Clean up DOI
            doi = doi.rstrip('.')
            return doi
    return None

def get_metadata_from_crossref(doi):
    """Fetch metadata from Crossref API using DOI."""
    try:
        headers = {
            'User-Agent': 'ReferenceFinder/1.0 (mailto:your-email@example.com)'
        }
        response = requests.get(f'https://api.crossref.org/works/{doi}', headers=headers)
        if response.status_code == 200:
            data = response.json()['message']
            
            # Extract author names
            authors = []
            if 'author' in data:
                for author in data['author']:
                    if 'given' in author and 'family' in author:
                        authors.append(f"{author['given']} {author['family']}")
                    elif 'family' in author:
                        authors.append(author['family'])
            
            # Extract publication date
            published_date = ''
            if 'published-print' in data:
                date_parts = data['published-print']['date-parts'][0]
                published_date = str(date_parts[0])  # Year
                if len(date_parts) > 1:
                    published_date += f"-{date_parts[1]:02d}"  # Month
                if len(date_parts) > 2:
                    published_date += f"-{date_parts[2]:02d}"  # Day
            
            return {
                'title': data.get('title', [''])[0],
                'authors': authors,
                'published_date': published_date,
                'doi': doi,
                'journal': data.get('container-title', [''])[0],
                'publisher': data.get('publisher', ''),
                'type': data.get('type', '')
            }
    except Exception as e:
        print(f"Error fetching metadata from Crossref: {str(e)}")
    return None

def extract_metadata(pdf_reader, file_path):
    """Extract metadata from PDF and enhance with Crossref data."""
    # First try to get DOI from PDF text
    doi = None
    text = ""
    
    # Try first few pages for DOI
    for i in range(min(3, len(pdf_reader.pages))):
        try:
            page_text = pdf_reader.pages[i].extract_text()
            text += page_text
            doi = extract_doi_from_text(page_text)
            if doi:
                break
        except Exception as e:
            print(f"Error extracting text from page {i}: {str(e)}")
    
    # If DOI found, try to get metadata from Crossref
    if doi:
        crossref_metadata = get_metadata_from_crossref(doi)
        if crossref_metadata:
            return crossref_metadata
    
    # Fallback to PDF metadata if Crossref fails
    try:
        info = pdf_reader.metadata
        if info:
            author = info.get('/Author', 'Unknown Author')
            title = info.get('/Title', 'Untitled')
            year = info.get('/CreationDate', '')
            if year and len(year) >= 4:
                year = year[2:6]
            else:
                year = 'Unknown Year'
                
            return {
                'title': title,
                'authors': [author] if author != 'Unknown Author' else [],
                'published_date': year,
                'doi': doi if doi else 'Not found',
                'journal': 'Unknown',
                'publisher': 'Unknown',
                'type': 'Unknown'
            }
    except Exception as e:
        print(f"Error extracting PDF metadata: {str(e)}")
    
    # Return default metadata if all else fails
    return {
        'title': 'Untitled',
        'authors': [],
        'published_date': 'Unknown',
        'doi': 'Not found',
        'journal': 'Unknown',
        'publisher': 'Unknown',
        'type': 'Unknown'
    }

def find_matching_quotes(text_by_page, search_text):
    """Find quotes from the PDF that contain the search terms."""
    search_terms = search_text.lower().split()
    matches = []
    
    # Look through each page
    for page_num, page_text in text_by_page.items():
        page_text_lower = page_text.lower()
        
        # Split text into sentences
        sentences = page_text.replace('\n', ' ').split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if all search terms are in this sentence
            sentence_lower = sentence.lower()
            if all(term in sentence_lower for term in search_terms):
                # Highlight matching terms
                highlighted_text = sentence
                for term in search_terms:
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    highlighted_text = pattern.sub(f"<mark>{term}</mark>", highlighted_text)
                
                matches.append({
                    'text': highlighted_text,
                    'page': page_num,
                    'terms': search_terms
                })
    
    return matches

@app.route('/pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'})
    
    file = request.files['file']
    search_text = request.form.get('text', '')
    
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Please upload a PDF file'})
    
    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the PDF
        pdf_reader = PdfReader(filepath)
        metadata = extract_metadata(pdf_reader, filepath)
        
        # Extract text from each page
        text_by_page = extract_text_from_pdf(filepath)
        
        # Find matching quotes
        matches = find_matching_quotes(text_by_page, search_text)
        
        # Add metadata to response
        response = {
            'results': matches,
            'pdf_url': f'http://localhost:5003/pdfs/{filename}',
            'metadata': metadata
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(port=5003, debug=True)
