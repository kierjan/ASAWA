import os
from flask import Flask, request, jsonify, render_template
from html import escape
from flask_sqlalchemy import SQLAlchemy
from textblob import TextBlob
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', handlers=[
    logging.FileHandler("error.log"),
    logging.StreamHandler()
])

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/reviews.db'
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
        sentiment = 'Positive' if analysis.sentiment.polarity > 0 else 'Negative'

        new_review = Review(review_text, aircraft_type, route, sentiment)
        db.session.add(new_review)
        db.session.commit()

        return jsonify({'reviewId': new_review.id, 'sentiment': new_review.sentiment})

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

if __name__ == '__main__':
    with app.app_context():
        instance_path = os.path.join(os.getcwd(), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        db.create_all()
    app.run(debug=True, host='0.0.0.0')