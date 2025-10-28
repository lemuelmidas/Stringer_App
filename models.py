from app import db

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
            "value": self.value,
            "length": self.length,
            "is_palindrome": self.is_palindrome,
            "unique_characters": self.unique_characters,
            "word_count": self.word_count,
            "sha256_hash": self.sha256_hash,
            "character_frequency_map": self.character_frequency_map
        }
