from flask import Flask, request, jsonify
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

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set NLTK data path to a writable directory
nltk_data_dir = "/tmp/nltk_data"
if not os.path.exists(nltk_data_dir):
    os.makedirs(nltk_data_dir)
nltk.data.path.append(nltk_data_dir)

# Download required NLTK data
try:
    nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
    nltk.download('stopwords', download_dir=nltk_data_dir, quiet=True)
    logger.info("NLTK data downloaded successfully")
except Exception as e:
    logger.error(f"Error downloading NLTK data: {str(e)}")
    logger.error(traceback.format_exc())

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(pdf_file):
    try:
        logger.info(f"Starting PDF extraction for file: {pdf_file.filename}")
        
        # Read the file content
        pdf_bytes = pdf_file.read()
        logger.info(f"Read {len(pdf_bytes)} bytes from file")
        
        # Create BytesIO object
        pdf_io = io.BytesIO(pdf_bytes)
        
        # Try to read the PDF
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_io)
            logger.info(f"PDF has {len(pdf_reader.pages)} pages")
        except Exception as e:
            logger.error(f"Error creating PDF reader: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception("Could not read the PDF file. Please make sure it's a valid PDF.")
        
        # Extract text
        text = ""
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                logger.info(f"Extracted {len(page_text) if page_text else 0} characters from page {i+1}")
            except Exception as e:
                logger.error(f"Error extracting text from page {i+1}: {str(e)}")
                continue
        
        if not text.strip():
            raise Exception("No text could be extracted from the PDF. The file might be scanned or protected.")
        
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text
        
    except Exception as e:
        logger.error(f"Error in extract_text_from_pdf: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def preprocess_text(text):
    try:
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        return text
    except Exception as e:
        logger.error(f"Error in preprocess_text: {str(e)}")
        raise

def find_similar_sentences(pdf_text, search_text, threshold=0.3):
    try:
        logger.info("Starting sentence similarity search")
        logger.info(f"Search text: {search_text}")
        
        # Tokenize PDF text into sentences
        sentences = sent_tokenize(pdf_text)
        logger.info(f"Found {len(sentences)} sentences in PDF")
        
        if not sentences:
            raise Exception("Could not identify any sentences in the PDF text")
        
        # Preprocess search text
        search_text = preprocess_text(search_text)
        search_words = set(word_tokenize(search_text))
        logger.info(f"Search terms: {search_words}")
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        search_words = search_words - stop_words
        logger.info(f"Search terms after stopword removal: {search_words}")
        
        if not search_words:
            raise Exception("No meaningful search terms found after preprocessing")
        
        similar_sentences = []
        
        for i, sentence in enumerate(sentences):
            try:
                # Preprocess sentence
                sentence = preprocess_text(sentence)
                sentence_words = set(word_tokenize(sentence))
                sentence_words = sentence_words - stop_words
                
                # Calculate similarity
                if sentence_words:
                    common_words = search_words.intersection(sentence_words)
                    similarity = len(common_words) / len(search_words)
                    
                    if similarity >= threshold:
                        similar_sentences.append({
                            'text': sentences[i],
                            'page': 1,
                            'similarity': float(similarity)
                        })
            except Exception as e:
                logger.error(f"Error processing sentence {i}: {str(e)}")
                continue
        
        logger.info(f"Found {len(similar_sentences)} similar sentences")
        return similar_sentences
        
    except Exception as e:
        logger.error(f"Error in find_similar_sentences: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.route('/', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        })

    try:
        logger.info("Received request")
        
        # Log request details
        logger.info(f"Files: {list(request.files.keys())}")
        logger.info(f"Form data: {list(request.form.keys())}")
        
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename:
            return jsonify({'error': 'No filename provided'}), 400
            
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400
        
        search_text = request.form.get('text', '').strip()
        if not search_text:
            return jsonify({'error': 'No search text provided'}), 400
        
        logger.info(f"Processing file: {file.filename}")
        logger.info(f"Search text: {search_text}")
        
        # Extract text from PDF
        try:
            pdf_text = extract_text_from_pdf(file)
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            return jsonify({'error': str(e)}), 400
        
        # Find similar sentences
        try:
            results = find_similar_sentences(pdf_text, search_text)
            logger.info(f"Returning {len(results)} results")
            return jsonify({'results': results or []})
        except Exception as e:
            logger.error(f"Text processing error: {str(e)}")
            return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

if __name__ == '__main__':
    app.run(port=5002, debug=True)
