from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
from collections import Counter
import os

app = Flask(__name__)

# -----------------------------
# Database configuration
# -----------------------------
# Ensure 'instance' folder exists
os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------
# Database model
# -----------------------------
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

# -----------------------------
# Utility function
# -----------------------------
def analyze_string(text):
    clean_text = text.strip()
    analysis = {
        "length": len(clean_text),
        "is_palindrome": clean_text.lower() == clean_text[::-1].lower(),
        "unique_characters": len(set(clean_text)),
        "word_count": len(clean_text.split()),
        "sha256_hash": hashlib.sha256(clean_text.encode()).hexdigest(),
        "character_frequency_map": dict(Counter(clean_text)),
    }
    return analysis

# -----------------------------
# Homepage
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to the String Analyzer API!",
        "available_endpoints": {
            "/strings/": "GET all strings, POST new string",
            "/strings/<value>/": "GET a single string",
            "/strings/<value>/delete/": "DELETE a string",
            "/strings/filter/": "GET with natural language filter, e.g., ?query=palindrome"
        }
    })

# -----------------------------
# Create / List Strings
# -----------------------------
@app.route("/strings/", methods=["GET", "POST"])
def strings():
    if request.method == "POST":
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "Missing 'value' field"}), 422

        value = data["value"]

        # Check duplicates
        if AnalyzedString.query.filter_by(value=value).first():
            return jsonify({"error": "String already analyzed"}), 409

        analyzed_data = analyze_string(value)
        new_string = AnalyzedString(value=value, **analyzed_data)
        db.session.add(new_string)
        db.session.commit()
        return jsonify(new_string.to_dict()), 201

    # GET all strings with optional filters
    query = AnalyzedString.query
    min_length = request.args.get("min_length", type=int)
    max_length = request.args.get("max_length", type=int)
    is_palindrome = request.args.get("is_palindrome")

    if min_length is not None:
        query = query.filter(AnalyzedString.length >= min_length)
    if max_length is not None:
        query = query.filter(AnalyzedString.length <= max_length)
    if is_palindrome is not None:
        query = query.filter(AnalyzedString.is_palindrome == (is_palindrome.lower() == "true"))

    results = [s.to_dict() for s in query.all()]
    return jsonify(results), 200

# -----------------------------
# Get / Delete single string
# -----------------------------
@app.route("/strings/<string:value>/", methods=["GET"])
def get_string(value):
    s = AnalyzedString.query.filter_by(value=value).first()
    if not s:
        return jsonify({"error": "String not found"}), 404
    return jsonify(s.to_dict()), 200

@app.route("/strings/<string:value>/delete/", methods=["DELETE"])
def delete_string(value):
    s = AnalyzedString.query.filter_by(value=value).first()
    if not s:
        return jsonify({"error": "String not found"}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Deleted successfully"}), 200

# -----------------------------
# Natural language filter
# -----------------------------
@app.route("/strings/filter/", methods=["GET"])
def filter_natural():
    query_param = request.args.get("query", "").lower()
    query = AnalyzedString.query

    if "palindrome" in query_param:
        query = query.filter(AnalyzedString.is_palindrome == True)
    if "longer than" in query_param:
        try:
            n = int(query_param.split("longer than")[1].split()[0])
            query = query.filter(AnalyzedString.length > n)
        except (ValueError, IndexError):
            pass
    if "shorter than" in query_param:
        try:
            n = int(query_param.split("shorter than")[1].split()[0])
            query = query.filter(AnalyzedString.length < n)
        except (ValueError, IndexError):
            pass

    results = [s.to_dict() for s in query.all()]
    return jsonify(results), 200

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
