import re
from typing import Tuple

STOPWORDS = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for'}

def remove_stopwords(query: str) -> str:
    """Remove common stopwords."""
    words = query.split()
    filtered = [w for w in words if w not in STOPWORDS]
    return ' '.join(filtered)

def clean_query(query: str) -> str:
    """Basic query cleaning: lowercase, strip, remove punctuation."""
    query = query.lower().strip()
    query = re.sub(r'[^a-z0-9\s]', '', query)  # Remove punctuation
    query = re.sub(r'\s+', ' ', query)  # Collapse whitespace
    return query

def detect_intent(query: str) -> str:
    """Very simple intent detection based on keywords."""
    q = query.lower().strip()
    if q.startswith(('how', 'what', 'why', 'who', 'where', 'when')):
        return 'informational'
    if any(word in q for word in ['buy', 'purchase', 'order', 'download']):
        return 'transactional'
    if any(word in q for word in ['login', 'homepage', 'open', 'go to']):
        return 'navigational'
    return 'unknown'

def process_query(query: str) -> Tuple[str, str]:
    """Clean query and detect intent."""
    cleaned = clean_query(query)
    cleaned = remove_stopwords(cleaned)  # Remove stopwords after cleaning
    intent = detect_intent(cleaned)
    return cleaned, intent
