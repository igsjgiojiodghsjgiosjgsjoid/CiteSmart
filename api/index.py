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

# Set NLTK data path to a writable directory
nltk.data.path.append("/tmp/nltk_data")

# Download required NLTK data
try:
    nltk.download('punkt', download_dir="/tmp/nltk_data")
    nltk.download('stopwords', download_dir="/tmp/nltk_data")
except Exception as e:
    print(f"Error downloading NLTK data: {str(e)}")

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(pdf_file):
    try:
        # Create a temporary file-like object
        pdf_bytes = pdf_file.read()
        pdf_io = io.BytesIO(pdf_bytes)
        
        # Try to read the PDF
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_io)
        except Exception as e:
            print(f"Error creating PDF reader: {str(e)}")
            raise Exception("Could not read the PDF file. Please make sure it's a valid PDF.")
        
        # Extract text
        text = ""
        for page in pdf_reader.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            except Exception as e:
                print(f"Error extracting text from page: {str(e)}")
                continue
        
        if not text.strip():
            raise Exception("No text could be extracted from the PDF. The file might be scanned or protected.")
        
        return text
        
    except Exception as e:
        print(f"Error in extract_text_from_pdf: {str(e)}")
        print(traceback.format_exc())
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
        print(f"Error in preprocess_text: {str(e)}")
        raise

def find_similar_sentences(pdf_text, search_text, threshold=0.3):
    try:
        # Tokenize PDF text into sentences
        sentences = sent_tokenize(pdf_text)
        if not sentences:
            raise Exception("Could not identify any sentences in the PDF text")
        
        # Preprocess search text
        search_text = preprocess_text(search_text)
        search_words = set(word_tokenize(search_text))
        
        # Remove stopwords from search words
        stop_words = set(stopwords.words('english'))
        search_words = search_words - stop_words
        
        if not search_words:
            raise Exception("No meaningful search terms found after preprocessing")
        
        similar_sentences = []
        
        for i, sentence in enumerate(sentences):
            try:
                # Preprocess sentence
                processed_sentence = preprocess_text(sentence)
                sentence_words = set(word_tokenize(processed_sentence))
                
                # Remove stopwords from sentence words
                sentence_words = sentence_words - stop_words
                
                # Calculate similarity
                if len(search_words) > 0 and len(sentence_words) > 0:
                    common_words = search_words.intersection(sentence_words)
                    similarity = len(common_words) / len(search_words)
                    
                    if similarity >= threshold:
                        similar_sentences.append({
                            'text': sentences[i],
                            'page': 1,
                            'similarity': float(similarity)
                        })
            except Exception as e:
                print(f"Error processing sentence {i}: {str(e)}")
                continue
        
        return similar_sentences
    except Exception as e:
        print(f"Error in find_similar_sentences: {str(e)}")
        print(traceback.format_exc())
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
        print("Received request")
        
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
        
        print(f"Processing file: {file.filename}")
        
        # Extract text from PDF
        try:
            pdf_text = extract_text_from_pdf(file)
        except Exception as e:
            print(f"PDF extraction error: {str(e)}")
            return jsonify({'error': str(e)}), 400
        
        # Find similar sentences
        try:
            results = find_similar_sentences(pdf_text, search_text)
            return jsonify({'results': results or []})
        except Exception as e:
            print(f"Text processing error: {str(e)}")
            return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

if __name__ == '__main__':
    app.run(port=5002, debug=True)
