from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
from collections import Counter
import os

# ----------------------------
# App setup
# ----------------------------
app = Flask(__name__)

# Ensure instance folder exists
os.makedirs(os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance"), exist_ok=True)

# Database config
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ----------------------------
# Model
# ----------------------------
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
            "character_frequency_map": self.character_frequency_map,
        }

# Create DB tables
with app.app_context():
    db.create_all()

# ----------------------------
# Helper function
# ----------------------------
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

# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def home():
    return """
    <html>
        <head><title>String Analyzer API</title></head>
        <body style="text-align:center; margin-top:50px; font-family:Arial;">
            <h1>Welcome to the String Analyzer API!</h1>
            <p><a href="/strings/">Click here</a> to explore all strings.</p>
        </body>
    </html>
    """

# POST /strings and GET /strings
@app.route("/strings/", methods=["GET", "POST"])
def list_create_strings():
    if request.method == "POST":
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "Missing 'value' field"}), 422

        value = data["value"]

        # Check duplicate
        if AnalyzedString.query.filter_by(value=value).first():
            return jsonify({"error": "String already analyzed"}), 409

        analysis = analyze_string(value)
        new_string = AnalyzedString(value=value, **analysis)
        db.session.add(new_string)
        db.session.commit()
        return jsonify(new_string.to_dict()), 201

    # GET /strings
    query = AnalyzedString.query

    # Optional filters
    min_length = request.args.get("min_length", type=int)
    max_length = request.args.get("max_length", type=int)
    is_palindrome = request.args.get("is_palindrome")

    if min_length is not None:
        query = query.filter(AnalyzedString.length >= min_length)
    if max_length is not None:
        query = query.filter(AnalyzedString.length <= max_length)
    if is_palindrome is not None:
        is_pal = is_palindrome.lower() == "true"
        query = query.filter(AnalyzedString.is_palindrome == is_pal)

    results = [s.to_dict() for s in query.all()]
    return jsonify(results), 200

# GET single string
@app.route("/strings/<string:value>/", methods=["GET"])
def get_string(value):
    string_obj = AnalyzedString.query.filter_by(value=value).first()
    if not string_obj:
        return jsonify({"error": "String not found"}), 404
    return jsonify(string_obj.to_dict()), 200

# DELETE string
@app.route("/strings/<string:value>/delete/", methods=["DELETE"])
def delete_string(value):
    string_obj = AnalyzedString.query.filter_by(value=value).first()
    if not string_obj:
        return jsonify({"error": "String not found"}), 404
    db.session.delete(string_obj)
    db.session.commit()
    return jsonify({"message": "Deleted successfully"}), 200

# GET /strings/filter-by-natural-language
@app.route("/strings/filter-by-natural-language", methods=["GET"])
def filter_natural_language():
    query_text = request.args.get("query", "").lower()
    query = AnalyzedString.query

    if "palindrome" in query_text:
        query = query.filter(AnalyzedString.is_palindrome == True)
    if "longer than" in query_text:
        try:
            n = int(query_text.split("longer than")[1].split()[0])
            query = query.filter(AnalyzedString.length > n)
        except:
            pass
    if "shorter than" in query_text:
        try:
            n = int(query_text.split("shorter than")[1].split()[0])
            query = query.filter(AnalyzedString.length < n)
        except:
            pass

    results = [s.to_dict() for s in query.all()]
    return jsonify(results), 200

# ----------------------------
# Run app
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
