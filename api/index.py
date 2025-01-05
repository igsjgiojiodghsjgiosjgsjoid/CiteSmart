from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import io
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

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
CORS(app)

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def find_similar_sentences(pdf_text, search_text, threshold=0.3):
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

def handler(request):
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            search_text = request.form.get('text', '')
            
            if not file or not search_text:
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(file)
            
            # Find similar sentences
            results = find_similar_sentences(pdf_text, search_text)
            
            return jsonify({'results': results})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Method not allowed'}), 405

# For local development
if __name__ == '__main__':
    app.run(port=5002)
