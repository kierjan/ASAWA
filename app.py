import os
from flask import Flask, request, jsonify, render_template, send_file, make_response
from io import StringIO
import csv
from html import escape
from flask_sqlalchemy import SQLAlchemy
from textblob import TextBlob
import logging
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', handlers=[
    logging.FileHandler("error.log"),
    logging.StreamHandler()
])

app = Flask(__name__)

# Define the absolute path for the database
database_path = os.path.join(os.path.abspath(os.getcwd()), 'instance', 'reviews.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_text = db.Column(db.String(500), nullable=False)
    aircraft_type = db.Column(db.String(100), nullable=False)
    route = db.Column(db.String(100), nullable=False)
    sentiment = db.Column(db.String(50), nullable=False)

    def __init__(self, review_text, aircraft_type, route, sentiment):
        self.review_text = review_text
        self.aircraft_type = aircraft_type
        self.route = route
        self.sentiment = sentiment

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        if not data:
            raise ValueError('No data provided')
        
        review_text = data.get('text')
        aircraft_type = data.get('aircraftType')
        route = data.get('route')

        if not review_text:
            raise ValueError('Review text is required')

        analysis = TextBlob(review_text)
        polarity = analysis.sentiment.polarity

        if polarity > 0.1:
            sentiment = 'Positive'
        elif polarity < -0.1:
            sentiment = 'Negative'
        else:
            sentiment = 'Neutral'

        new_review = Review(review_text, aircraft_type, route, sentiment)
        db.session.add(new_review)
        db.session.commit()

        return jsonify({
            'reviewId': new_review.id, 
            'sentiment': new_review.sentiment,
            'reviewText': new_review.review_text,
            'aircraftType': new_review.aircraft_type,
            'route': new_review.route
        })

    except Exception as e:
        logging.error(f"Error analyzing review: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/reviews', methods=['GET'])
def get_reviews():
    try:
        reviews = Review.query.all()
        reviews_list = [
            {
                'reviewId': review.id,
                'reviewText': escape(review.review_text),
                'aircraftType': review.aircraft_type,
                'route': review.route,
                'sentiment': review.sentiment
            }
            for review in reviews
        ]
        return jsonify(reviews_list)
    
    except Exception as e:
        logging.error(f"Error fetching reviews: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download_reviews():
    try:
        reviews = Review.query.all()
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Review ID', 'Review Text', 'Aircraft Type', 'Route', 'Sentiment'])
        for review in reviews:
            cw.writerow([review.id, review.review_text, review.aircraft_type, review.route, review.sentiment])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=reviews.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        logging.error(f"Error downloading reviews: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    try:
        # Example labeled data for evaluation
        labeled_reviews = [
            {"text": "The flight was fantastic!", "label": "Positive"},
            {"text": "The service was terrible and the seats were uncomfortable.", "label": "Negative"},
            {"text": "It was an okay experience, nothing special.", "label": "Neutral"},
            {"text": "Loved the food and the staff were friendly!", "label": "Positive"},
            {"text": "The plane was delayed and the staff were rude.", "label": "Negative"},
            # Add more labeled reviews as needed
        ]

        def predict_sentiment(text):
            analysis = TextBlob(text)
            polarity = analysis.sentiment.polarity
            if polarity > 0.1:
                return "Positive"
            elif polarity < -0.1:
                return "Negative"
            else:
                return "Neutral"

        predicted_labels = [predict_sentiment(review["text"]) for review in labeled_reviews]
        true_labels = [review["label"] for review in labeled_reviews]

        accuracy = accuracy_score(true_labels, predicted_labels)
        precision = precision_score(true_labels, predicted_labels, average='weighted')
        recall = recall_score(true_labels, predicted_labels, average='weighted')
        f1 = f1_score(true_labels, predicted_labels, average='weighted')

        return jsonify({
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        })
    except Exception as e:
        logging.error(f"Error calculating metrics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        instance_path = os.path.join(os.getcwd(), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        db.create_all()
    app.run(debug=True, host='0.0.0.0')