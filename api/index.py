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

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        raise Exception("Failed to extract text from PDF. Please make sure it's a valid PDF file.")

def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def find_similar_sentences(pdf_text, search_text, threshold=0.3):
    try:
        # Tokenize PDF text into sentences
        sentences = sent_tokenize(pdf_text)
        
        # Preprocess search text
        search_text = preprocess_text(search_text)
        search_words = set(word_tokenize(search_text))
        
        # Remove stopwords from search words
        stop_words = set(stopwords.words('english'))
        search_words = search_words - stop_words
        
        similar_sentences = []
        
        for i, sentence in enumerate(sentences):
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
                        'page': 1,  # You might want to track page numbers
                        'similarity': similarity
                    })
        
        # Sort by similarity score
        similar_sentences.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_sentences
    except Exception as e:
        print(f"Error finding similar sentences: {str(e)}")
        raise Exception("Failed to process text comparison")

@app.route('/', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    if request.method == 'POST':
        try:
            print("Received request")
            
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            search_text = request.form.get('text', '')
            
            if not file:
                return jsonify({'error': 'No file selected'}), 400
            
            if not search_text:
                return jsonify({'error': 'No search text provided'}), 400
            
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'Only PDF files are supported'}), 400
            
            print(f"Processing file: {file.filename}")
            
            # Extract text from PDF
            try:
                pdf_text = extract_text_from_pdf(file)
            except Exception as e:
                print(f"PDF extraction error: {str(e)}")
                return jsonify({'error': str(e)}), 400
            
            if not pdf_text.strip():
                return jsonify({'error': 'Could not extract text from PDF'}), 400
            
            # Find similar sentences
            try:
                results = find_similar_sentences(pdf_text, search_text)
            except Exception as e:
                print(f"Text processing error: {str(e)}")
                return jsonify({'error': str(e)}), 400
            
            if not results:
                return jsonify({'results': [], 'message': 'No matching references found'}), 200
            
            print(f"Found {len(results)} matches")
            return jsonify({'results': results})
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': 'An unexpected error occurred'}), 500

    return jsonify({'error': 'Method not allowed'}), 405

# For local development
if __name__ == '__main__':
    app.run(port=5002, debug=True)
