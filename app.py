# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
from collections import Counter
import os

# ---------------------------
# Initialize Flask app
# ---------------------------
app = Flask(__name__)

# ---------------------------
# Configure database
# ---------------------------
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "app.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Ensure folder exists
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------------
# Database model
# ---------------------------
class AnalyzedString(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Text, unique=True, nullable=False)
    length = db.Column(db.Integer, nullable=False)
    is_palindrome = db.Column(db.Boolean, nullable=False)
    unique_characters = db.Column(db.Integer, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)
    sha256_hash = db.Column(db.String(64), nullable=False)
    character_frequency_map = db.Column(db.JSON, nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "value": self.value,
            "length": self.length,
            "is_palindrome": self.is_palindrome,
            "unique_characters": self.unique_characters,
            "word_count": self.word_count,
            "sha256_hash": self.sha256_hash,
            "character_frequency_map": self.character_frequency_map,
        }

# ---------------------------
# Helper function
# ---------------------------
def analyze_string(text):
    clean_text = text.strip()
    return {
        "length": len(clean_text),
        "is_palindrome": clean_text.lower() == clean_text[::-1].lower(),
        "unique_characters": len(set(clean_text)),
        "word_count": len(clean_text.split()),
        "sha256_hash": hashlib.sha256(clean_text.encode()).hexdigest(),
        "character_frequency_map": dict(Counter(clean_text)),
    }

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>String Analyzer API</title>
            <style>
                body { font-family: Arial; text-align:center; margin-top:150px; }
                a { color: #007bff; text-decoration:none; font-weight:bold; }
                a:hover { text-decoration:underline; }
            </style>
        </head>
        <body>
            <h1>Welcome to the String Analyzer API!</h1>
            <p><a href="/strings/">Click here</a> to explore the API.</p>
        </body>
    </html>
    """

# Create & analyze a new string
@app.route('/strings/', methods=['POST'])
def create_string():
    data = request.get_json()
    if not data or 'value' not in data:
        return jsonify({"error": "Missing 'value' field"}), 422

    value = data['value']

    # Prevent duplicates
    if AnalyzedString.query.filter_by(value=value).first():
        return jsonify({"error": "String already analyzed"}), 409

    analyzed_data = analyze_string(value)
    new_string = AnalyzedString(value=value, **analyzed_data)
    db.session.add(new_string)
    db.session.commit()
    return jsonify(new_string.serialize()), 201

# Get all strings
@app.route('/strings/', methods=['GET'])
def get_all_strings():
    query = AnalyzedString.query

    # Optional filters
    min_length = request.args.get('min_length', type=int)
    max_length = request.args.get('max_length', type=int)
    is_palindrome = request.args.get('is_palindrome')

    if min_length is not None:
        query = query.filter(AnalyzedString.length >= min_length)
    if max_length is not None:
        query = query.filter(AnalyzedString.length <= max_length)
    if is_palindrome is not None:
        val = is_palindrome.lower() == "true"
        query = query.filter(AnalyzedString.is_palindrome == val)

    results = query.all()
    return jsonify([s.serialize() for s in results]), 200

# Get single string
@app.route('/strings/<string:value>/', methods=['GET'])
def get_string(value):
    s = AnalyzedString.query.filter_by(value=value).first()
    if not s:
        return jsonify({"error": "String not found"}), 404
    return jsonify(s.serialize()), 200

# Delete string
@app.route('/strings/<string:value>/delete/', methods=['DELETE'])
def delete_string(value):
    s = AnalyzedString.query.filter_by(value=value).first()
    if not s:
        return jsonify({"error": "String not found"}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Deleted successfully"}), 200

# Natural language filter
@app.route('/strings/filter-by-natural-language', methods=['GET'])
def filter_natural_language():
    query_param = request.args.get('query', '').lower()
    query = AnalyzedString.query

    if 'palindrome' in query_param:
        query = query.filter(AnalyzedString.is_palindrome == True)
    if 'longer than' in query_param:
        try:
            number = int(query_param.split('longer than')[1].split()[0])
            query = query.filter(AnalyzedString.length > number)
        except:
            pass
    if 'shorter than' in query_param:
        try:
            number = int(query_param.split('shorter than')[1].split()[0])
            query = query.filter(AnalyzedString.length < number)
        except:
            pass

    results = query.all()
    return jsonify([s.serialize() for s in results]), 200

# ---------------------------
# Run app
# ---------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
