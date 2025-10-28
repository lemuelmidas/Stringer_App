import hashlib
from collections import Counter

def analyze_string(text):
    text = text.strip()
    return {
        "length": len(text),
        "is_palindrome": text.lower() == text[::-1].lower(),
        "unique_characters": len(set(text)),
        "word_count": len(text.split()),
        "sha256_hash": hashlib.sha256(text.encode()).hexdigest(),
        "character_frequency_map": dict(Counter(text))
    }
