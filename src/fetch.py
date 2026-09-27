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


def fetch_recent_articles(sources, max_articles_per_day=10, hours=24):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []

    for source in sources:
        try:
            feed = feedparser.parse(source["url"])

            # feedparser spesso non solleva eccezioni per feed malformati:
            # controlliamo anche bozo_exception.
            if getattr(feed, "bozo", 0):
                bozo_exception = getattr(feed, "bozo_exception", None)
                print(
                    f"   ⚠ RSS problematico: {source['name']}"
                    + (
                        f" ({type(bozo_exception).__name__}: {bozo_exception})"
                        if bozo_exception
                        else ""
                    )
                )

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

            print(f"   ✓ RSS: {source['name']}")

        except Exception as e:
            print(
                f"   ⚠ RSS fallito: {source['name']} — "
                f"{type(e).__name__}: {e}"
            )
            continue

    return articles[:max_articles_per_day]


def _get_published_date(entry):
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None
