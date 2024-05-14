from flask import Flask, jsonify, request, render_template
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
import hashlib
import time

app = Flask(__name__)

# Initialize NLTK resources once
nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
stop_words = stopwords.words('english')
lemmatizer = WordNetLemmatizer()

def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    filtered_tokens = [token for token in tokens if token not in stop_words]
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]
    processed_text = ' '.join(lemmatized_tokens)
    return processed_text

def generate_hash_id(text):
    hash_object = hashlib.sha256()
    hash_object.update(text.encode('utf-8'))
    return hash_object.hexdigest()[:8]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        text = data['text']
        aircraft_type = data['aircraftType']
        route = data['route']
        processed_text = preprocess_text(text)
        sia = SentimentIntensityAnalyzer()
        score = sia.polarity_scores(processed_text)
        sentiment = 'positive' if score['compound'] > 0 else 'negative' if score['compound'] < 0 else 'neutral'
        review_id = generate_hash_id(text + str(time.time()))
        return jsonify({'sentiment': sentiment, 'reviewId': review_id, 'aircraftType': aircraft_type, 'route': route})
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080)