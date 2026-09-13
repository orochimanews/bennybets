import unicodedata
import re
from typing import Tuple, Optional

KNOWN_ALIASES = {
    'psg': 'paris saint germain',
    'paris sg': 'paris saint germain',
    'om': 'marseille',
    'olympique marseille': 'marseille',
    'olympique de marseille': 'marseille',
    'ol': 'lyon',
    'olympique lyon': 'lyon',
    'olympique lyonnais': 'lyon',
    'losc': 'lille',
    'asse': 'saint etienne',
    'man city': 'manchester city',
    'man utd': 'manchester united',
    'man united': 'manchester united',
    'atletico': 'atletico madrid',
    'ath bilbao': 'athletic bilbao',
    'athletic club': 'athletic bilbao',
    'bayern': 'bayern munich',
    'dortmund': 'borussia dortmund',
    'bvb': 'borussia dortmund',
    'inter': 'inter milan',
    'internazionale': 'inter milan',
    'juve': 'juventus',
    'sporting cp': 'sporting lisbonne',
    'sporting': 'sporting lisbonne',
    'benfica': 'benfica lisbonne',
    'paris st g': 'paris saint germain',
    'paris saint g': 'paris saint germain',
    'paris st germain': 'paris saint germain',
    'estac troyes': 'troyes',
    'estac': 'troyes',
    'fc utrecht': 'utrecht',
    'tokyo v': 'tokyo verdy',
}

STOP_WORDS = {
    'fc', 'cf', 'as', 'sc', 'rc', 'ogc', 'ac', 'athletic', 'club', 'sporting',
    'cd', 'fk', 'sk', 'us', 'ss', 'tsv', 'vfb', 'calcio', 'de', 'le', 'la', 'les',
    'du', 'des', 'united', 'city', 'town', 'wanderers', 'rovers', 'hotspur', 'olympique'
}

def clean_text(text: str) -> str:
    if not text:
        return ''
    nfkd = unicodedata.normalize('NFKD', text)
    clean = ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()
    clean = re.sub(r'[-_/.,\']', ' ', clean)
    clean = re.sub(r'\bst\b', 'saint', clean)
    clean = re.sub(r'\bste\b', 'sainte', clean)
    return ' '.join(clean.split())

def normalize_team_name(name: str) -> str:
    cleaned = clean_text(name)
    if cleaned in KNOWN_ALIASES:
        return KNOWN_ALIASES[cleaned]
    
    words = cleaned.split()
    filtered = [w for w in words if w not in STOP_WORDS]
    result = ' '.join(filtered) if filtered else cleaned
    
    if result in KNOWN_ALIASES:
        return KNOWN_ALIASES[result]
    return result

def similarity_ratio(a: str, b: str) -> float:
    set_a = set(a.split())
    set_b = set(b.split())
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    jaccard = intersection / union if union > 0 else 0.0
    
    if set_a.issubset(set_b) or set_b.issubset(set_a):
        return max(jaccard, 0.85)
    return jaccard

def are_teams_matching(team1: str, team2: str, threshold: float = 0.65) -> bool:
    norm1 = normalize_team_name(team1)
    norm2 = normalize_team_name(team2)
    if norm1 == norm2:
        return True
    return similarity_ratio(norm1, norm2) >= threshold

def generate_match_key(home: str, away: str, sport: str = 'football') -> str:
    norm_home = normalize_team_name(home)
    norm_away = normalize_team_name(away)
    return f'{sport}:{norm_home}_vs_{norm_away}'
