from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from hashlib import sha256
from collections import Counter

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --------------------------
# Models
# --------------------------
class AnalyzedString(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Text, unique=True, nullable=False)
    length = db.Column(db.Integer)
    is_palindrome = db.Column(db.Boolean)
    unique_characters = db.Column(db.Integer)
    word_count = db.Column(db.Integer)
    sha256_hash = db.Column(db.String(64))
    character_frequency_map = db.Column(db.JSON)

    def to_dict(self):
        return {
            "id": self.id,
            "value": self.value,
            "length": self.length,
            "is_palindrome": self.is_palindrome,
            "unique_characters": self.unique_characters,
            "word_count": self.word_count,
            "sha256_hash": self.sha256_hash,
            "character_frequency_map": self.character_frequency_map
        }

# --------------------------
# Utility
# --------------------------
def analyze_string(text):
    clean_text = text.strip()
    return {
        "length": len(clean_text),
        "is_palindrome": clean_text.lower() == clean_text[::-1].lower(),
        "unique_characters": len(set(clean_text)),
        "word_count": len(clean_text.split()),
        "sha256_hash": sha256(clean_text.encode()).hexdigest(),
        "character_frequency_map": dict(Counter(clean_text))
    }

# --------------------------
# Routes
# --------------------------
@app.route('/')
def home():
    return """
        <html>
            <head>
                <title>String Analyzer API</title>
                <style>
                    body {font-family: Arial; text-align:center; margin-top:150px;}
                    a {color:#007bff; font-weight:bold; text-decoration:none;}
                    a:hover {text-decoration:underline;}
                </style>
            </head>
            <body>
                <h1>Welcome to the String Analyzer API!</h1>
                <p><a href="/strings">Click here</a> to explore the API.</p>
            </body>
        </html>
    """

@app.route('/strings', methods=['POST', 'GET'])
def strings():
    if request.method == 'POST':
        data = request.get_json()
        value = data.get('value')
        if not value:
            return jsonify({"error": "Missing 'value' field"}), 400

        # Prevent duplicates
        existing = AnalyzedString.query.filter_by(value=value).first()
        if existing:
            return jsonify({"error": "String already analyzed"}), 409

        analysis = analyze_string(value)
        new_string = AnalyzedString(value=value, **analysis)
        db.session.add(new_string)
        db.session.commit()
        return jsonify(new_string.to_dict()), 201

    # GET all strings with optional filters
    query = AnalyzedString.query
    min_length = request.args.get('min_length', type=int)
    max_length = request.args.get('max_length', type=int)
    is_palindrome = request.args.get('is_palindrome')
    
    if min_length is not None:
        query = query.filter(AnalyzedString.length >= min_length)
    if max_length is not None:
        query = query.filter(AnalyzedString.length <= max_length)
    if is_palindrome is not None:
        query = query.filter(AnalyzedString.is_palindrome == (is_palindrome.lower()=='true'))

    results = query.all()
    return jsonify([s.to_dict() for s in results]), 200

@app.route('/strings/<string:value>', methods=['GET', 'DELETE'])
def string_detail(value):
    s = AnalyzedString.query.filter_by(value=value).first()
    if not s:
        return jsonify({"error": "String not found"}), 404

    if request.method == 'GET':
        return jsonify(s.to_dict()), 200

    # DELETE
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Deleted successfully"}), 200

@app.route('/strings/filter-by-natural-language', methods=['GET'])
def natural_language_filter():
    query_text = request.args.get('query', '').lower()
    query = AnalyzedString.query

    if 'palindrome' in query_text:
        query = query.filter(AnalyzedString.is_palindrome == True)
    if 'longer than' in query_text:
        try:
            n = int(query_text.split('longer than')[1].split()[0])
            query = query.filter(AnalyzedString.length > n)
        except:
            pass
    if 'shorter than' in query_text:
        try:
            n = int(query_text.split('shorter than')[1].split()[0])
            query = query.filter(AnalyzedString.length < n)
        except:
            pass

    results = query.all()
    return jsonify([s.to_dict() for s in results]), 200

# --------------------------
# Run
# --------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
