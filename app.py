from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
from collections import Counter
import os

app = Flask(__name__)

# ------------------------------
# Database configuration
# ------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ------------------------------
# Models
# ------------------------------
class AnalyzedString(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Text, unique=True, nullable=False)
    length = db.Column(db.Integer)
    is_palindrome = db.Column(db.Boolean)
    unique_characters = db.Column(db.Integer)
    word_count = db.Column(db.Integer)
    sha256_hash = db.Column(db.String(64))
    character_frequency_map = db.Column(db.JSON)

    def __repr__(self):
        return f"<AnalyzedString {self.value}>"

# ------------------------------
# Utils
# ------------------------------
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

# ------------------------------
# Routes
# ------------------------------
@app.route("/")
def home():
    return """
        <h1>Welcome to the String Analyzer API!</h1>
        <p><a href="/strings/">Click here</a> to explore the API.</p>
    """

@app.route("/strings/", methods=["GET", "POST"])
def strings():
    if request.method == "POST":
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "Missing 'value' field"}), 400

        value = data["value"]
        if AnalyzedString.query.filter_by(value=value).first():
            return jsonify({"error": "String already analyzed"}), 409

        analyzed_data = analyze_string(value)
        new_string = AnalyzedString(value=value, **analyzed_data)
        db.session.add(new_string)
        db.session.commit()
        return jsonify({
            "id": new_string.id,
            "value": new_string.value,
            **analyzed_data
        }), 201

    # GET all strings
    results = AnalyzedString.query.all()
    return jsonify([{
        "id": s.id,
        "value": s.value,
        "length": s.length,
        "is_palindrome": s.is_palindrome,
        "unique_characters": s.unique_characters,
        "word_count": s.word_count,
        "sha256_hash": s.sha256_hash,
        "character_frequency_map": s.character_frequency_map
    } for s in results]), 200

@app.route("/strings/<string:text_value>/delete/", methods=["DELETE"])
def delete_string(text_value):
    s = AnalyzedString.query.filter_by(value=text_value).first()
    if not s:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Deleted successfully"}), 200

# ------------------------------
# Run on Railway
# ------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
