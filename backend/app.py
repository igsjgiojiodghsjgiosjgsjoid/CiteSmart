from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PyPDF2 import PdfReader
from nltk.tokenize import sent_tokenize
import re
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app)

def extract_pdf_metadata(pdf_reader):
    """Extract metadata from PDF by analyzing the content."""
    try:
        # Get text from first few pages
        first_pages_text = ""
        for page in pdf_reader.pages[:3]:
            first_pages_text += page.extract_text()
        
        # Look for author patterns
        author = None
        author_patterns = [
            r'by\s*([\w\s\.,]+?)(?:\d|Abstract|Introduction|$)',
            r'Author[s]?[:;\s]+([\w\s\.,]+?)(?:\d|Abstract|Introduction|$)',
            r'([\w\s\.,]+?)\s*\(?\d{4}\)?[,\s]*Department',
            r'([\w\s\.,]+?)\s*\(?\d{4}\)?[,\s]*University',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, first_pages_text, re.IGNORECASE)
            if match:
                author = match.group(1).strip()
                # Clean up author name
                author = re.sub(r'\s+', ' ', author)
                author = author.strip('., ')
                break
        
        # If no author found, try metadata
        if not author:
            metadata = pdf_reader.metadata
            if metadata and metadata.get('/Author'):
                author = metadata.get('/Author').strip()
        
        # Default if still no author
        author = author or 'Unknown Author'
        
        # Look for year patterns
        year = None
        year_patterns = [
            r'(\d{4})',
            r'copyright\s*(\d{4})',
            r'published\s*in\s*(\d{4})',
            r'(\d{4})\s*\.',
            r'\((\d{4})\)',
            r'[\s,.](\d{4})[\s,.]',
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, first_pages_text, re.IGNORECASE)
            if match:
                year = match.group(1)
                break
        
        # If no year found, try metadata
        if not year and pdf_reader.metadata:
            for key in ['/CreationDate', '/ModDate']:
                date = pdf_reader.metadata.get(key, '')
                if date:
                    year_match = re.search(r'(\d{4})', str(date))
                    if year_match:
                        year = year_match.group(1)
                        break
        
        # Default if still no year
        year = year or str(datetime.now().year)
        
        print(f"Extracted metadata - Author: {author}, Year: {year}")
        return author, year
        
    except Exception as e:
        print(f"Error extracting metadata: {str(e)}")
        return 'Unknown Author', str(datetime.now().year)

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

def find_page_number(text_by_page, quote_text):
    """Find the actual page number where the quote appears."""
    for page_num, page_text in text_by_page.items():
        # Clean and normalize texts for comparison
        clean_page = ' '.join(page_text.split())
        clean_quote = ' '.join(quote_text.split())
        
        if clean_quote in clean_page:
            return page_num
    return 1  # fallback to page 1 if not found

def normalize_text(text):
    """Normalize text by removing extra spaces and newlines."""
    # Remove extra whitespace and normalize spaces
    return ' '.join(text.split())

def find_matching_quotes(text_by_page, search_text):
    """Find quotes from the PDF that contain the search terms."""
    search_terms = [term.lower() for term in search_text.split()]
    matches = []
    
    print(f"Searching for terms: {search_terms}")
    
    for page_num, page_text in text_by_page.items():
        # Create a clean version for searching but keep original for display
        clean_page = ' '.join(page_text.split())
        sentences = sent_tokenize(clean_page)
        
        # Look for matches in groups of sentences
        for i in range(len(sentences)):
            current_sentence = sentences[i].strip()
            current_lower = current_sentence.lower()
            
            # Check if any search term is in the current sentence
            matching_terms = [term for term in search_terms 
                            if term in current_lower]
            
            if matching_terms:
                # Get surrounding context
                start_idx = max(0, i - 1)
                end_idx = min(len(sentences), i + 2)
                context_sentences = sentences[start_idx:end_idx]
                
                # Create a clean version of the quote for searching
                clean_quote = ' '.join(context_sentences)
                
                # Find the quote in the original text by matching first and last words
                quote_words = clean_quote.split()
                first_word = re.escape(quote_words[0])
                last_word = re.escape(quote_words[-1])
                
                # Create a pattern that matches from first word to last word
                pattern = f"{first_word}.*?{last_word}"
                
                # Find the quote in the original text
                match = re.search(pattern, page_text, re.DOTALL)
                if match:
                    exact_quote = match.group(0)
                    
                    matches.append({
                        'quote': exact_quote,
                        'page': page_num,
                        'relevance': len(matching_terms),
                        'highlighted_terms': matching_terms
                    })
                    print(f"Found match on page {page_num} with {len(matching_terms)} matching terms")
    
    # Sort by relevance
    matches.sort(key=lambda x: x['relevance'], reverse=True)
    print(f"Found {len(matches)} total matching quotes")
    return matches  # Return all matches instead of limiting to 5

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    """Serve the PDF file."""
    try:
        return send_from_directory('uploads', filename)
    except Exception as e:
        return str(e), 404

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and search."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        search_text = request.form.get('searchText', '').strip()
        
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not search_text:
            return jsonify({'error': 'No search text provided'}), 400
        
        # Save the file with a secure filename
        filename = secure_filename(file.filename)
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        # Process the PDF
        text_by_page = {}
        try:
            with open(filepath, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                author, year = extract_pdf_metadata(pdf_reader)
                text_by_page = extract_text_from_pdf(pdf_file)
                
                if not text_by_page:
                    return jsonify({'error': 'Could not extract text from PDF'}), 400
                
                # Find matching quotes
                quotes = find_matching_quotes(text_by_page, search_text)
                
                # Add citation to each quote
                for quote in quotes:
                    quote['citation'] = f'({author}, {year}, p. {quote["page"]})'
                
                return jsonify({
                    'quotes': quotes,
                    'filename': filename
                })
                
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return jsonify({'error': f'Failed to process PDF: {str(e)}'}), 400
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5002, debug=True)
