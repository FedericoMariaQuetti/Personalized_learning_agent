"""
fetch.py
--------
Scarica gli articoli pubblicati nelle ultime 24 ore dai feed RSS
elencati in config/sources.yaml. Usato solo per la sezione "News" (8/8).
"""

import feedparser
import yaml
from datetime import datetime, timedelta, timezone


def load_sources(config_path="config/sources.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["sources"], config.get("settings", {})


def fetch_recent_articles(sources, max_articles_per_day=15, hours=24):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []

    for source in sources:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries:
            published = _get_published_date(entry)
            if published is None or published < cutoff:
                continue
            articles.append({
                "title": entry.get("title", "Senza titolo"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:500],
                "source": source["name"],
            })

    return articles[:max_articles_per_day]


def _get_published_date(entry):
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None
