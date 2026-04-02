"""
scrapers/doctissimo_scraper.py — Scraper Google News RSS (FR)
Surveille les actualités et discussions parentalité francophones
via les flux RSS Google News — jamais bloqués, toujours à jour.
"""

import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

GOOGLE_NEWS_FEEDS = [
    {
        "name": "Google News — histoires enfants",
        "url": "https://news.google.com/rss/search?q=histoire+enfant+personnalis%C3%A9e&hl=fr&gl=FR&ceid=FR:fr",
    },
    {
        "name": "Google News — application enfant lecture",
        "url": "https://news.google.com/rss/search?q=application+enfant+lecture&hl=fr&gl=FR&ceid=FR:fr",
    },
    {
        "name": "Google News — alternatives écrans enfants",
        "url": "https://news.google.com/rss/search?q=alternatives+%C3%A9crans+enfants&hl=fr&gl=FR&ceid=FR:fr",
    },
    {
        "name": "Google News — parentalité numérique",
        "url": "https://news.google.com/rss/search?q=parentalit%C3%A9+num%C3%A9rique+enfant&hl=fr&gl=FR&ceid=FR:fr",
    },
]

HEADERS = {
    "User-Agent": "NoctilioMonitor/1.0 RSS Reader"
}


def scrape_doctissimo() -> list[dict]:
    """
    Récupère les derniers articles/discussions via Google News RSS.
    Retourne une liste de dicts normalisés.
    """
    posts = []

    for feed in GOOGLE_NEWS_FEEDS:
        try:
            response = requests.get(feed["url"], headers=HEADERS, timeout=15)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")

                title = title_el.text if title_el is not None else ""
                url = link_el.text if link_el is not None else ""
                body = desc_el.text if desc_el is not None else ""

                if not title or len(title) < 10:
                    continue

                posts.append({
                    "title": title,
                    "body": body[:300] if body else "",
                    "url": url,
                    "source": feed["name"],
                    "author": "",
                    "created_at": datetime.now(timezone.utc).timestamp(),
                    "upvotes": 0,
                    "num_comments": 0,
                })

            time.sleep(1)

        except requests.RequestException as e:
            print(f"    [Google News] Erreur sur {feed['name']}: {e}")
            continue
        except ET.ParseError as e:
            print(f"    [Google News] Erreur XML sur {feed['name']}: {e}")
            continue

    print(f"    [Google News FR] {len(posts)} articles récupérés.")
    return posts
