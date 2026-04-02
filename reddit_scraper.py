"""
scrapers/reddit_scraper.py — Scraper Reddit
Utilise l'API JSON publique de Reddit (sans clé) pour surveiller
les subreddits pertinents parentalité / enfants.
"""

import time
import requests

# ──────────────────────────────────────────────
# Subreddits à surveiller
# On mélange FR et EN pour maximiser la couverture
# ──────────────────────────────────────────────
SUBREDDITS = [
    "france",           # Discussions générales FR — parentalité y apparaît souvent
    "french",           # Communauté francophone internationale
    "Parenting",        # Subreddit EN parenting très actif
    "Parents",          # Autre communauté parenting EN
    "raisingkids",      # Spécialisé éducation enfants
    "beyondthebump",    # Parents de jeunes enfants
    "Mommit",           # Communauté mères
    "daddit",           # Communauté pères
    "KidsAreFuckingStupid",  # Viral, beaucoup de parents actifs
    "AskParents",       # Questions parentalité
]

# L'API JSON publique Reddit — pas besoin de compte
REDDIT_JSON_URL = "https://www.reddit.com/r/{subreddit}/new.json?limit=25"

HEADERS = {
    # Reddit bloque les User-Agents génériques — on se présente comme un bot légitime
    "User-Agent": "NoctilioMonitor/1.0 (monitoring app for parenting discussions; contact: marvincohen95@gmail.com)"
}


def scrape_reddit() -> list[dict]:
    """
    Récupère les 25 derniers posts de chaque subreddit surveillé.
    Retourne une liste de dicts normalisés {title, url, body, source, created_at}.
    """
    posts = []

    for subreddit in SUBREDDITS:
        try:
            url = REDDIT_JSON_URL.format(subreddit=subreddit)
            response = requests.get(url, headers=HEADERS, timeout=10)

            # Reddit peut retourner 429 si on va trop vite
            if response.status_code == 429:
                print(f"    [Reddit] Rate limit sur r/{subreddit}, pause 5s...")
                time.sleep(5)
                response = requests.get(url, headers=HEADERS, timeout=10)

            response.raise_for_status()
            data = response.json()

            for item in data.get("data", {}).get("children", []):
                post_data = item.get("data", {})

                # Ignorer les posts supprimés ou sans contenu utile
                if post_data.get("removed_by_category"):
                    continue

                posts.append({
                    "title": post_data.get("title", ""),
                    # selftext = corps du post (vide pour les liens)
                    "body": post_data.get("selftext", "")[:500],
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "source": f"Reddit r/{subreddit}",
                    "author": post_data.get("author", ""),
                    "created_at": post_data.get("created_utc", 0),
                    "upvotes": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                })

            # Pause polie entre chaque subreddit pour respecter Reddit
            time.sleep(1.5)

        except requests.RequestException as e:
            print(f"    [Reddit] Erreur sur r/{subreddit}: {e}")
            continue

    print(f"    [Reddit] {len(posts)} posts récupérés.")
    return posts
