"""
scrapers/doctissimo_scraper.py — Scraper Doctissimo
Surveille les forums Doctissimo (famille, enfants, éducation)
en scrapant les pages publiques de listing de topics.
"""

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Forums Doctissimo à surveiller
# URLs des pages de listing des derniers sujets
# ──────────────────────────────────────────────
DOCTISSIMO_FORUMS = [
    {
        "name": "Doctissimo — Bébé & enfant",
        "url": "https://forum.doctissimo.fr/famille/bebe-enfant/liste_sujet-1.htm",
    },
    {
        "name": "Doctissimo — Éducation",
        "url": "https://forum.doctissimo.fr/famille/education/liste_sujet-1.htm",
    },
    {
        "name": "Doctissimo — Vie de famille",
        "url": "https://forum.doctissimo.fr/famille/vie-de-famille/liste_sujet-1.htm",
    },
    {
        "name": "Doctissimo — École & apprentissage",
        "url": "https://forum.doctissimo.fr/famille/ecole/liste_sujet-1.htm",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NoctilioBot/1.0; +https://noctilio.com)",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_doctissimo() -> list[dict]:
    """
    Scrape les titres des derniers sujets sur les forums Doctissimo ciblés.
    Retourne une liste de dicts normalisés.
    """
    posts = []

    for forum in DOCTISSIMO_FORUMS:
        try:
            response = requests.get(forum["url"], headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Doctissimo liste les sujets dans des <tr> avec classe "sujet"
            # On cherche les liens vers les topics individuels
            topic_links = soup.select("a.sujet_link, a[href*='/liste_message']")

            if not topic_links:
                # Fallback : on cherche tous les liens qui ressemblent à des topics
                topic_links = soup.find_all("a", href=lambda h: h and "liste_message" in str(h))

            for link in topic_links[:20]:  # Max 20 sujets par forum
                title = link.get_text(strip=True)

                # Ignorer les titres vides ou trop courts (menus, etc.)
                if not title or len(title) < 10:
                    continue

                topic_url = link.get("href", "")
                if not topic_url.startswith("http"):
                    topic_url = "https://forum.doctissimo.fr" + topic_url

                posts.append({
                    "title": title,
                    "body": "",  # On ne charge pas chaque page topic pour éviter le ban
                    "url": topic_url,
                    "source": forum["name"],
                    "author": "",
                    "created_at": datetime.now(timezone.utc).timestamp(),
                    "upvotes": 0,
                    "num_comments": 0,
                })

            # Pause polie entre les requêtes
            time.sleep(2)

        except requests.RequestException as e:
            print(f"    [Doctissimo] Erreur sur {forum['name']}: {e}")
            continue
        except Exception as e:
            print(f"    [Doctissimo] Erreur de parsing sur {forum['name']}: {e}")
            continue

    print(f"    [Doctissimo] {len(posts)} sujets récupérés.")
    return posts
