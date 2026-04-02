# 🌙 Noctilio Monitor

Agent de monitoring qui surveille les forums parentalité (Reddit, Doctissimo, Mumsnet)
et t'alerte sur Slack quand une discussion pertinente apparaît.

**Principe** : l'agent trouve les opportunités, *toi* tu réponds humainement.
Pas de bot qui poste automatiquement — juste un radar pour ne rien manquer.

---

## Architecture

```
monitor.py              ← Point d'entrée principal
scrapers/
  reddit_scraper.py     ← API JSON publique Reddit
  doctissimo_scraper.py ← Scraping HTML forums Doctissimo
  mumsnet_scraper.py    ← Scraping HTML forums Mumsnet
utils/
  scorer.py             ← Moteur de scoring 0-100
  slack_notifier.py     ← Envoi digest Slack (Block Kit)
.github/workflows/
  monitor.yml           ← GitHub Actions (toutes les 6h)
seen_posts.json         ← Cache auto-généré (ne pas modifier)
```

---

## Installation (5 minutes)

### 1. Forker / cloner ce repo sur GitHub

```bash
git clone https://github.com/TON_USERNAME/noctilio-monitor.git
cd noctilio-monitor
```

### 2. Créer un webhook Slack

1. Va sur [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → From scratch → Nom : "Noctilio Monitor"
3. Dans le menu gauche : **Incoming Webhooks** → Activer
4. **Add New Webhook to Workspace** → Choisir ton channel (ex: `#monitoring`)
5. Copie l'URL du webhook (commence par `https://hooks.slack.com/services/...`)

### 3. Ajouter le secret dans GitHub

1. Ton repo GitHub → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
   - Name : `SLACK_WEBHOOK_URL`
   - Value : l'URL copiée à l'étape 2

### 4. Activer GitHub Actions

1. Onglet **Actions** de ton repo
2. Si désactivé, cliquer "I understand my workflows, go ahead and enable them"
3. Le workflow se lancera automatiquement à la prochaine heure prévue (7h, 13h, 19h, 23h UTC)

### 5. Tester immédiatement

1. Onglet **Actions** → **Noctilio Monitor** → **Run workflow** → Run
2. Le workflow tourne ~2 minutes, puis tu reçois le Slack (si des posts pertinents existent)

---

## Personnalisation

### Modifier les mots-clés (`utils/scorer.py`)

```python
HIGH_VALUE_KEYWORDS = [
    "histoire pour enfant",  # ← Ajoute tes propres mots-clés ici
    "histoire personnalisée",
    ...
]
```

Les trois niveaux :
- `HIGH_VALUE_KEYWORDS` → +20 pts chacun (max 60 pts)
- `RELEVANT_KEYWORDS` → +10 pts chacun (max 30 pts)
- `WEAK_KEYWORDS` → +5 pts chacun (max 10 pts)

### Modifier le seuil d'alerte (`monitor.py`)

```python
THRESHOLD = 55  # Baisser pour avoir plus d'alertes, monter pour filtrer davantage
```

### Modifier la fréquence (`monitor.yml`)

```yaml
schedule:
  - cron: "0 7,13,19,23 * * *"  # Modifier les heures UTC ici
```

### Ajouter des subreddits (`scrapers/reddit_scraper.py`)

```python
SUBREDDITS = [
    "france",
    "Parenting",
    "MonNouveauSubreddit",  # ← Ajouter ici
]
```

---

## Comment répondre (guide rapide)

Quand tu reçois une alerte Slack :

1. **Clique** sur le lien du post
2. **Lis** la discussion complète pour comprendre le contexte
3. **Réponds** en apportant de la valeur réelle (conseil, expérience, ressource)
4. **Mentionne Noctilio** seulement si c'est naturellement pertinent et utile
   - ✅ "j'ai eu le même problème, j'utilise une app qui génère des histoires perso..."
   - ❌ "hey check out noctilio.com c'est trop bien !!"

Le signal de qualité : ta réponse serait utile *même sans mentionner Noctilio*.

---

## Coût

**Zéro.** GitHub Actions offre 2000 minutes/mois sur les repos publics (illimité).
Chaque run prend ~2 minutes → 8 runs/jour → ~480 minutes/mois → bien en dessous de la limite.

Sur un repo privé : 500 minutes/mois gratuites, suffisant pour 3-4 runs/jour.
