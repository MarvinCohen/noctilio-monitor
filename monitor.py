"""
monitor.py — Agent de monitoring Noctilio
Surveille Reddit, Doctissimo et Mumsnet pour détecter les discussions
pertinentes liées à la parentalité / histoires enfants / lecture.
Envoie une alerte Slack avec les meilleures opportunités.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from scrapers.reddit_scraper import scrape_reddit
from scrapers.doctissimo_scraper import scrape_doctissimo
from scrapers.mumsnet_scraper import scrape_mumsnet
from utils.scorer import score_post
from utils.slack_notifier import send_slack_digest


# ──────────────────────────────────────────────
# Configuration du seuil de pertinence (0-100)
# Seuls les posts avec score >= THRESHOLD sont alertés
# ──────────────────────────────────────────────
THRESHOLD = 55

# Fichier de cache pour ne pas re-alerter les mêmes posts
CACHE_FILE = "seen_posts.json"


def load_cache() -> set:
    """Charge les IDs de posts déjà vus depuis le cache JSON."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_cache(seen_ids: set):
    """Sauvegarde le cache des posts déjà vus."""
    # On garde seulement les 2000 derniers IDs pour éviter un fichier trop grand
    ids_list = list(seen_ids)[-2000:]
    with open(CACHE_FILE, "w") as f:
        json.dump(ids_list, f)


def make_post_id(post: dict) -> str:
    """Génère un identifiant unique pour un post à partir de son URL."""
    return hashlib.md5(post["url"].encode()).hexdigest()


def run():
    """Point d'entrée principal : scrape, score, filtre, notifie."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] Démarrage du monitoring Noctilio...")

    seen_ids = load_cache()
    all_posts = []

    # ── Scraping de chaque source ──
    print("→ Scraping Reddit...")
    all_posts += scrape_reddit()

    print("→ Scraping Doctissimo...")
    all_posts += scrape_doctissimo()

    print("→ Scraping Mumsnet...")
    all_posts += scrape_mumsnet()

    print(f"  {len(all_posts)} posts récupérés au total.")

    # ── Déduplication + scoring ──
    new_relevant = []

    for post in all_posts:
        post_id = make_post_id(post)

        # Ignorer les posts déjà vus
        if post_id in seen_ids:
            continue

        seen_ids.add(post_id)

        # Calculer le score de pertinence (0-100)
        post["score"] = score_post(post)

        # Garder seulement les posts au-dessus du seuil
        if post["score"] >= THRESHOLD:
            new_relevant.append(post)

    # ── Tri par score décroissant ──
    new_relevant.sort(key=lambda p: p["score"], reverse=True)

    print(f"  {len(new_relevant)} posts pertinents trouvés (seuil: {THRESHOLD}).")

    # ── Envoi Slack ──
    if new_relevant:
        send_slack_digest(new_relevant)
        print(f"  ✓ Alerte Slack envoyée pour {len(new_relevant)} posts.")
    else:
        print("  Aucun nouveau post pertinent. Pas d'alerte envoyée.")

    # ── Sauvegarde du cache ──
    save_cache(seen_ids)
    print("  ✓ Cache mis à jour.")


if __name__ == "__main__":
    run()
