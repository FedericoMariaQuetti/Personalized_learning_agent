"""
compose.py
----------
Costruisce il contenuto dell'email giornaliera e salva una copia
nel log settimanale (data/weekly_log.json), che verrà poi usato
per generare il resoconto scaricabile.
"""

import json
import os
from datetime import date


LOG_PATH = "data/weekly_log.json"


def build_daily_email_html(summary_text, articles, day=None):
    """Crea il contenuto HTML della mail giornaliera."""
    day = day or date.today().isoformat()

    links_html = "".join(
        f'<li><a href="{a["link"]}">{a["title"]}</a> — <em>{a["source"]}</em></li>'
        for a in articles
    )

    html = f"""
    <html>
      <body style="font-family: sans-serif; max-width: 600px; margin: auto;">
        <h2>Newsletter del {day}</h2>
        <div style="white-space: pre-wrap;">{summary_text}</div>
        <hr>
        <h3>Fonti</h3>
        <ul>{links_html}</ul>
      </body>
    </html>
    """
    return html


def append_to_weekly_log(summary_text, articles, day=None):
    """Aggiunge il riassunto di oggi al file di log settimanale."""
    day = day or date.today().isoformat()

    log = _load_log()
    log["entries"].append({
        "date": day,
        "summary": summary_text,
        "articles": articles,
    })
    _save_log(log)


def _load_log():
    if not os.path.exists(LOG_PATH):
        return {"entries": []}
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_log(log):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
