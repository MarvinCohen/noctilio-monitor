"""
scrapers/mumsnet_scraper.py — Scraper Mumsnet
Surveille les forums Mumsnet (parenting UK, très actif)
en scrapant les listes de topics publiques.
"""

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Forums Mumsnet à surveiller
# Mumsnet est anglophone mais très influent en parenting
# ──────────────────────────────────────────────
MUMSNET_FORUMS = [
    {
        "name": "Mumsnet — Children's Books",
        "url": "https://www.mumsnet.com/talk/childrens_books",
    },
    {
        "name": "Mumsnet — Children's Health",
        "url": "https://www.mumsnet.com/talk/childrens_health",
    },
    {
        "name": "Mumsnet — Parenting",
        "url": "https://www.mumsnet.com/talk/parenting",
    },
    {
        "name": "Mumsnet — Primary Education",
        "url": "https://www.mumsnet.com/talk/primary_education",
    },
    {
        "name": "Mumsnet — Sleep",
        "url": "https://www.mumsnet.com/talk/sleep",
    },
    {
        "name": "Mumsnet — Arts & Crafts",
        "url": "https://www.mumsnet.com/talk/arts_and_crafts",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_mumsnet() -> list[dict]:
    """
    Scrape les titres des derniers sujets sur les forums Mumsnet ciblés.
    Retourne une liste de dicts normalisés.
    """
    posts = []

    for forum in MUMSNET_FORUMS:
        try:
            response = requests.get(forum["url"], headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Mumsnet liste les threads dans des liens avec data-testid ou classes spécifiques
            # On cherche les titres de threads — plusieurs sélecteurs en fallback
            thread_links = (
                soup.select("a[data-testid='thread-title']") or
                soup.select("a.thread-title") or
                soup.select(".threadlist a[href*='/talk/']") or
                soup.find_all("a", href=lambda h: h and "/talk/" in str(h) and h.count("/") >= 4)
            )

            seen_urls = set()  # Déduplication locale par forum

            for link in thread_links[:20]:
                title = link.get_text(strip=True)

                if not title or len(title) < 10:
                    continue

                thread_url = link.get("href", "")
                if not thread_url.startswith("http"):
                    thread_url = "https://www.mumsnet.com" + thread_url

                # Éviter les doublons de liens dans la même page
                if thread_url in seen_urls:
                    continue
                seen_urls.add(thread_url)

                posts.append({
                    "title": title,
                    "body": "",
                    "url": thread_url,
                    "source": forum["name"],
                    "author": "",
                    "created_at": datetime.now(timezone.utc).timestamp(),
                    "upvotes": 0,
                    "num_comments": 0,
                })

            time.sleep(2)

        except requests.RequestException as e:
            print(f"    [Mumsnet] Erreur sur {forum['name']}: {e}")
            continue
        except Exception as e:
            print(f"    [Mumsnet] Erreur de parsing sur {forum['name']}: {e}")
            continue

    print(f"    [Mumsnet] {len(posts)} sujets récupérés.")
    return posts
