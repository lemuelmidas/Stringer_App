import hashlib
from collections import Counter

def analyze_string(value: str) -> dict:
    clean_value = value.strip()
    return {
        "length": len(clean_value),
        "is_palindrome": clean_value.lower() == clean_value[::-1].lower(),
        "unique_characters": len(set(clean_value)),
        "word_count": len(clean_value.split()),
        "sha256_hash": hashlib.sha256(clean_value.encode()).hexdigest(),
        "character_frequency_map": dict(Counter(clean_value)),
    }
