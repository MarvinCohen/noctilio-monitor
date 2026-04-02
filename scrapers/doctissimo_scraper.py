"""
scrapers/doctissimo_scraper.py — Scraper forums FR parentalité
Surveille Magicmaman et Parents.fr (Doctissimo ayant restructuré ses URLs).
"""

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

FORUMS = [
    {
        "name": "Magicmaman — Forum enfants",
        "url": "https://forum.magicmaman.com/enfants/",
    },
    {
        "name": "Magicmaman — Forum éducation",
        "url": "https://forum.magicmaman.com/education/",
    },
    {
        "name": "Magicmaman — Forum bébé",
        "url": "https://forum.magicmaman.com/bebe/",
    },
    {
        "name": "Forum Parents.fr",
        "url": "https://www.parents.fr/forum/",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_doctissimo() -> list[dict]:
    """
    Scrape les forums FR parentalité (Magicmaman, Parents.fr).
    Retourne une liste de dicts normalisés.
    """
    posts = []

    for forum in FORUMS:
        try:
            response = requests.get(forum["url"], headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Cherche tous les liens qui ressemblent à des topics de forum
            all_links = soup.find_all("a", href=True)
            seen_urls = set()

            for link in all_links:
                title = link.get_text(strip=True)
                href = link.get("href", "")

                if not title or len(title) < 15:
                    continue

                # Filtrer les liens de navigation (menus, catégories)
                if any(skip in title.lower() for skip in ["connexion", "inscription", "accueil", "forum", "retour", "page", "suivant", "précédent"]):
                    continue

                if not href.startswith("http"):
                    href = forum["url"].rstrip("/") + "/" + href.lstrip("/")

                if href in seen_urls:
                    continue
                seen_urls.add(href)

                posts.append({
                    "title": title,
                    "body": "",
                    "url": href,
                    "source": forum["name"],
                    "author": "",
                    "created_at": datetime.now(timezone.utc).timestamp(),
                    "upvotes": 0,
                    "num_comments": 0,
                })

            time.sleep(2)

        except requests.RequestException as e:
            print(f"    [Forums FR] Erreur sur {forum['name']}: {e}")
            continue
        except Exception as e:
            print(f"    [Forums FR] Erreur parsing {forum['name']}: {e}")
            continue

    print(f"    [Forums FR] {len(posts)} sujets récupérés.")
    return posts
