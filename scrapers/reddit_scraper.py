"""
scrapers/reddit_scraper.py — Scraper Reddit via RSS
Utilise les flux RSS publics de Reddit (pas de clé API requise)
qui ne sont pas bloqués par les serveurs GitHub Actions.
"""

import time
import requests
import xml.etree.ElementTree as ET

SUBREDDITS = [
    "france",
    "french",
    "Parenting",
    "Parents",
    "raisingkids",
    "beyondthebump",
    "Mommit",
    "daddit",
    "AskParents",
]

REDDIT_RSS_URL = "https://www.reddit.com/r/{subreddit}/new/.rss?limit=25"

HEADERS = {
    "User-Agent": "NoctilioMonitor/1.0 RSS Reader (contact: marvincohen95@gmail.com)"
}

NS = {"atom": "http://www.w3.org/2005/Atom"}


def scrape_reddit() -> list[dict]:
    posts = []

    for subreddit in SUBREDDITS:
        try:
            url = REDDIT_RSS_URL.format(subreddit=subreddit)
            response = requests.get(url, headers=HEADERS, timeout=15)

            if response.status_code == 429:
                print(f"    [Reddit] Rate limit sur r/{subreddit}, pause 10s...")
                time.sleep(10)
                response = requests.get(url, headers=HEADERS, timeout=15)

            response.raise_for_status()

            root = ET.fromstring(response.content)

            for entry in root.findall("atom:entry", NS):
                title_el = entry.find("atom:title", NS)
                link_el = entry.find("atom:link", NS)
                content_el = entry.find("atom:content", NS)
                author_el = entry.find("atom:author/atom:name", NS)

                title = title_el.text if title_el is not None else ""
                url_post = link_el.get("href", "") if link_el is not None else ""
                body = content_el.text if content_el is not None else ""

                if not title or len(title) < 5:
                    continue

                posts.append({
                    "title": title,
                    "body": body[:300] if body else "",
                    "url": url_post,
                    "source": f"Reddit r/{subreddit}",
                    "author": author_el.text if author_el is not None else "",
                    "created_at": 0,
                    "upvotes": 0,
                    "num_comments": 0,
                })

            time.sleep(2)

        except requests.RequestException as e:
            print(f"    [Reddit] Erreur sur r/{subreddit}: {e}")
            continue
        except ET.ParseError as e:
            print(f"    [Reddit] Erreur XML sur r/{subreddit}: {e}")
            continue

    print(f"    [Reddit] {len(posts)} posts récupérés.")
    return posts
