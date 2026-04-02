"""
utils/slack_notifier.py — Envoi des alertes vers Slack
Utilise le Block Kit de Slack pour un message bien formaté
avec les posts groupés par source et triés par score.
"""

import os
import json
import requests
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# URL du webhook Slack (définie comme variable d'environnement)
# À créer sur : https://api.slack.com/apps → Incoming Webhooks
# ──────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Emojis par niveau de score pour rendre le digest lisible d'un coup d'œil
SCORE_EMOJI = {
    90: "🔥",  # Score >= 90 : opportunité exceptionnelle
    70: "⭐",  # Score >= 70 : très pertinent
    55: "👀",  # Score >= 55 : à regarder
}

# Couleur de la sidebar Slack selon le score max du digest
SCORE_COLOR = {
    90: "#E8593C",  # Rouge-orangé : brûlant
    70: "#F2A623",  # Amber : chaud
    55: "#1D9E75",  # Teal : normal
}


def get_score_emoji(score: int) -> str:
    """Retourne l'emoji correspondant au niveau de score."""
    for threshold, emoji in SCORE_EMOJI.items():
        if score >= threshold:
            return emoji
    return "👀"


def get_color(posts: list[dict]) -> str:
    """Couleur de la sidebar selon le meilleur score du digest."""
    max_score = max(p["score"] for p in posts) if posts else 0
    for threshold, color in SCORE_COLOR.items():
        if max_score >= threshold:
            return color
    return SCORE_COLOR[55]


def format_post_block(post: dict) -> dict:
    """
    Formate un post en bloc Slack Section avec lien cliquable.
    Retourne un Block Kit section block.
    """
    emoji = get_score_emoji(post["score"])
    title = post["title"][:80] + ("..." if len(post["title"]) > 80 else "")
    source = post["source"]
    score = post["score"]
    url = post["url"]

    # Corps du message Slack (markdown Slack)
    text = f"{emoji} *<{url}|{title}>*\n"
    text += f"_{source}_ · Score : *{score}/100*"

    # Ajouter les infos d'engagement pour Reddit
    if post.get("upvotes", 0) > 0:
        text += f" · ↑{post['upvotes']} · 💬{post['num_comments']}"

    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text},
    }


def build_slack_message(posts: list[dict]) -> dict:
    """
    Construit le payload Slack complet avec Block Kit.
    Groupe les posts par source pour plus de lisibilité.
    """
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y à %Hh%M UTC")
    count = len(posts)
    max_score = max(p["score"] for p in posts) if posts else 0

    blocks = []

    # ── En-tête ──
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"🌙 Noctilio Monitor — {count} opportunité{'s' if count > 1 else ''} détectée{'s' if count > 1 else ''}",
            "emoji": True,
        },
    })

    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"Rapport du {now} · Meilleur score : *{max_score}/100*",
        }],
    })

    blocks.append({"type": "divider"})

    # ── Conseil d'action ──
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "*Comment répondre ?* Clique sur le lien, lis le contexte, "
                "réponds authentiquement en apportant de la valeur. "
                "Mentionne Noctilio *seulement* si c'est naturel et pertinent."
            ),
        },
    })

    blocks.append({"type": "divider"})

    # ── Posts groupés par source ──
    sources_seen = []
    posts_by_source: dict[str, list] = {}

    for post in posts:
        src = post["source"]
        if src not in posts_by_source:
            posts_by_source[src] = []
            sources_seen.append(src)
        posts_by_source[src].append(post)

    for source in sources_seen:
        source_posts = posts_by_source[source]

        # Titre de la source
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{source}*"},
        })

        # Posts de cette source (max 5 par source pour ne pas surcharger)
        for post in source_posts[:5]:
            blocks.append(format_post_block(post))

        blocks.append({"type": "divider"})

    # ── Pied de page ──
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": "Noctilio Monitor · GitHub Actions · Pour modifier les mots-clés : `utils/scorer.py`",
        }],
    })

    return {
        "text": f"🌙 Noctilio : {count} nouvelle(s) opportunité(s) de discussion !",
        "attachments": [{
            "color": get_color(posts),
            "blocks": blocks,
        }],
    }


def send_slack_digest(posts: list[dict]) -> bool:
    """
    Envoie le digest Slack.
    Retourne True si succès, False sinon.
    """
    if not SLACK_WEBHOOK_URL:
        print("    [Slack] SLACK_WEBHOOK_URL non définie — impossible d'envoyer.")
        return False

    payload = build_slack_message(posts)

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()

        if response.text == "ok":
            return True
        else:
            print(f"    [Slack] Réponse inattendue : {response.text}")
            return False

    except requests.RequestException as e:
        print(f"    [Slack] Erreur d'envoi : {e}")
        return False
