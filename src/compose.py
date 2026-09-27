"""
compose.py
----------
Assembla l'email giornaliera con tutte le sezioni (1-8) e aggiorna il log
settimanale usato per generare il resoconto scaricabile.
"""

import json
import os
from datetime import date

LOG_PATH = "data/weekly_log.json"

FEEDBACK_FOOTER = """
<h2>7. Feedback</h2>
<p>Rispondi direttamente a questa email per: cambiare argomenti, aumentare o
ridurre la profondità, adattare la difficoltà, registrare le tue risposte
agli esercizi, aggiungere richieste al percorso, o correggere qualcosa.
Il sistema legge la tua risposta e aggiorna il percorso automaticamente.</p>
"""


def build_full_email_html(sections_html, news_html, day=None):
    """
    sections_html: lista di stringhe HTML già pronte per le sezioni 1-6
                    (Science, Reading, Philosophy, German, Coding, Poker)
    news_html: HTML della sezione 8 (News/RSS)
    """
    day = day or date.today().isoformat()

    body = "\n".join(sections_html) + FEEDBACK_FOOTER + news_html

    return f"""
    <html>
      <body style="font-family: sans-serif; max-width: 700px; margin: auto; line-height: 1.5;">
        <h1>Il tuo percorso di oggi — {day}</h1>
        {body}
      </body>
    </html>
    """


def build_news_html(summary_text, articles):
    links_html = "".join(
        f'<li><a href="{a["link"]}">{a["title"]}</a> — <em>{a["source"]}</em></li>'
        for a in articles
    )
    return f"""
    <h2>8. News</h2>
    <div style="white-space: pre-wrap;">{summary_text}</div>
    <ul>{links_html}</ul>
    """


def append_to_weekly_log(day_entry, day=None):
    """
    day_entry: dizionario con il contenuto testuale (non HTML) di ogni sezione
    del giorno, così il resoconto settimanale resta leggibile come testo.
    """
    day = day or date.today().isoformat()
    log = _load_log()
    log["entries"].append({"date": day, **day_entry})
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
