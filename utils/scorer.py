"""
utils/scorer.py — Moteur de scoring de pertinence
Attribue un score 0-100 à chaque post selon sa pertinence pour Noctilio.
Plus le score est élevé, plus c'est une opportunité d'intervenir.

Logique de scoring :
  - Mots-clés "haute valeur" → +20 pts chacun (max 3 = 60 pts)
  - Mots-clés "pertinents" → +10 pts chacun (max 3 = 30 pts)
  - Mots-clés "signal faible" → +5 pts chacun (max 2 = 10 pts)
  - Bonus question (?, comment, aide) → +10 pts
  - Bonus engagement Reddit (upvotes, comments) → jusqu'à +10 pts
  - Malus hors-sujet évident → -30 pts
"""

import re

# ──────────────────────────────────────────────
# Mots-clés haute valeur — le post parle exactement de ce que Noctilio résout
# ──────────────────────────────────────────────
HIGH_VALUE_KEYWORDS = [
    # FR — histoires
    "histoire pour enfant", "histoire enfant", "histoires enfants",
    "histoire du soir", "histoire personnalisée", "conte personnalisé",
    "raconter une histoire", "histoire bedtime", "histoire à dormir",
    # FR — lecture / app
    "app lecture enfant", "application enfant", "appli enfant",
    "application lecture", "lecture enfant", "apprendre à lire",
    "livre personnalisé", "livre pour enfant", "album personnalisé",
    # FR — IA / génération
    "ia pour enfant", "intelligence artificielle enfant", "histoire ia",
    "générer histoire", "histoire générée", "histoire créée",
    # EN — stories
    "bedtime story", "bedtime stories", "personalized story",
    "personalised story", "children's story", "story for kids",
    "kids story app", "story app", "ai story", "story generator",
    "reading app for kids", "custom story", "make up a story",
]

# ──────────────────────────────────────────────
# Mots-clés pertinents — signal fort mais moins direct
# ──────────────────────────────────────────────
RELEVANT_KEYWORDS = [
    # FR — enfants / parentalité
    "mon enfant", "ma fille", "mon fils", "mes enfants",
    "alternative écran", "alternatives aux écrans", "sans écran",
    "activité enfant", "activités enfants", "éveil enfant",
    "coucher enfant", "routine du soir", "ritual soir",
    "imagination enfant", "créativité enfant",
    "cadeau enfant", "idée cadeau", "noël enfant",
    "6 ans", "7 ans", "8 ans", "5 ans", "4 ans", "9 ans", "10 ans",
    # EN — parenting signals
    "my kid", "my child", "my daughter", "my son", "toddler",
    "screen time", "no screens", "bedtime routine",
    "imaginative play", "creative kids", "reading to kids",
    "kids app", "children app", "educational app",
]

# ──────────────────────────────────────────────
# Mots-clés signal faible — contexte parental général
# ──────────────────────────────────────────────
WEAK_KEYWORDS = [
    "parent", "parents", "maman", "papa", "famille",
    "enfant", "enfants", "bébé", "kid", "kids", "children",
    "school", "école", "maternelle", "primaire",
    "lire", "lecture", "livre", "book", "reading",
]

# ──────────────────────────────────────────────
# Mots-clés hors-sujet — on pénalise pour éviter le bruit
# ──────────────────────────────────────────────
OFFTOPIC_KEYWORDS = [
    "divorce", "garde d'enfant", "pension alimentaire", "avocat",
    "vaccination", "vaccin", "maladie", "médecin", "urgences",
    "accident", "violence", "abus", "maltraitance",
    "politique", "élection", "gouvernement",
    "immobilier", "crédit", "prêt",
]

# Termes indiquant une question / demande d'aide (opportunité d'intervenir)
QUESTION_SIGNALS = [
    "?", "comment", "aide", "conseil", "recommand",
    "suggestion", "help", "advice", "recommend", "any idea",
    "quelqu'un", "someone", "anyone",
]


def normalize(text: str) -> str:
    """Normalise le texte : minuscules, supprime les accents pour matching flexible."""
    text = text.lower()
    # Normalisation des accents courants en français
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a",
        "ù": "u", "û": "u", "ü": "u",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ç": "c",
    }
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)
    return text


def count_keyword_matches(text: str, keywords: list[str]) -> int:
    """Compte combien de mots-clés de la liste sont présents dans le texte."""
    normalized_text = normalize(text)
    count = 0
    for kw in keywords:
        if normalize(kw) in normalized_text:
            count += 1
    return count


def score_post(post: dict) -> int:
    """
    Calcule le score de pertinence d'un post (0-100).
    Plus le score est élevé, plus c'est une opportunité pour Noctilio.
    """
    # Texte complet à analyser (titre + corps)
    full_text = f"{post.get('title', '')} {post.get('body', '')}"

    score = 0

    # ── Mots-clés haute valeur (plafond à 3 matchs = 60 pts) ──
    high_matches = min(count_keyword_matches(full_text, HIGH_VALUE_KEYWORDS), 3)
    score += high_matches * 20

    # ── Mots-clés pertinents (plafond à 3 matchs = 30 pts) ──
    relevant_matches = min(count_keyword_matches(full_text, RELEVANT_KEYWORDS), 3)
    score += relevant_matches * 10

    # ── Mots-clés signal faible (plafond à 2 matchs = 10 pts) ──
    weak_matches = min(count_keyword_matches(full_text, WEAK_KEYWORDS), 2)
    score += weak_matches * 5

    # ── Bonus question / demande d'aide (+10) ──
    for signal in QUESTION_SIGNALS:
        if signal in full_text.lower():
            score += 10
            break  # Un seul bonus par post

    # ── Bonus engagement Reddit (upvotes + commentaires) → max +10 pts ──
    upvotes = post.get("upvotes", 0)
    comments = post.get("num_comments", 0)
    if upvotes > 50 or comments > 10:
        score += 10
    elif upvotes > 10 or comments > 3:
        score += 5

    # ── Malus hors-sujet (-30) ──
    offtopic_count = count_keyword_matches(full_text, OFFTOPIC_KEYWORDS)
    if offtopic_count > 0:
        score -= 30

    # ── Clamp entre 0 et 100 ──
    return max(0, min(100, score))
