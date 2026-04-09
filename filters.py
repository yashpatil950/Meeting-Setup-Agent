# filters.py
from typing import List

CS_KEYWORDS = [
    "computer science", "csce", "cs seminar", "machine learning", "ai", "systems",
    "distributed", "databases", "security", "algorithms", "vision", "nlp", "hci",
]
TAMU_KEYWORDS = ["tamu", "texas a&m", "aggies", "college station", "csce@tamu"]

def is_relevant(subject: str, body: str) -> bool:
    text = f"{subject}\n{body}".lower()
    return any(k in text for k in CS_KEYWORDS) or any(k in text for k in TAMU_KEYWORDS)
