"""
main.py
-------
Punto di ingresso. Ogni giorno:
  1. Legge il feedback nuovo dalle risposte email e aggiorna lo stato
  2. Genera il contenuto di oggi per le 6 sezioni del curriculum
  3. Genera la sezione News (RSS)
  4. Compone e invia l'email completa
  5. Salva lo stato aggiornato e registra il giorno nel log settimanale
  6. Se è il giorno impostato, genera il resoconto settimanale scaricabile
"""

from datetime import date

import state as state_module
import feedback
import fetch
import summarize
import compose
import send_email
import weekly_report

from content.science import generate_science_section
from content.reading import generate_reading_section
from content.philosophy import generate_philosophy_section
from content.german import generate_german_section
from content.coding import generate_coding_section
from content.poker import generate_poker_section


def main():
    curriculum_state = state_module.load_state()

    print("1/6 - Controllo il feedback nelle risposte email...")
    recipients = [r.strip() for r in _get_env("RECIPIENT_EMAIL").split(",")]
    feedback_log_before = len(curriculum_state.get("feedback_log", []))
    try:
        curriculum_state = feedback.process_feedback(
            curriculum_state,
            gmail_user=_get_env("GMAIL_USER"),
            gmail_password=_get_env("GMAIL_APP_PASSWORD"),
            allowed_senders=recipients,
        )
    except Exception as e:
        # Il feedback è "best effort": se fallisce, la newsletter di oggi deve
        # comunque partire. L'errore resta visibile nei log di GitHub Actions.
        print(f"   Attenzione: lettura feedback fallita ({e}). Proseguo senza applicare modifiche.")
    new_feedback_changes = [
        entry["change"] for entry in curriculum_state.get("feedback_log", [])[feedback_log_before:]
    ]
    print(f"   {len(new_feedback_changes)} modifiche applicate dal feedback.")

    print("2/6 - Genero le sezioni del curriculum (Science, Reading, Philosophy, German, Coding, Poker)...")
    science_html, curriculum_state["science"], science_log = generate_science_section(curriculum_state["science"])
    reading_html, curriculum_state["reading"], reading_log = generate_reading_section(curriculum_state["reading"])
    philosophy_html, curriculum_state["philosophy"], philosophy_log = generate_philosophy_section(curriculum_state["philosophy"])
    german_html, curriculum_state["german"], german_log = generate_german_section(curriculum_state["german"])
    coding_html, curriculum_state["coding"], coding_log = generate_coding_section(curriculum_state["coding"])
    poker_html, curriculum_state["poker"], poker_log = generate_poker_section(curriculum_state["poker"])

    print("3/6 - Genero la sezione News (RSS)...")
    sources, settings = fetch.load_sources()
    articles = fetch.fetch_recent_articles(sources, max_articles_per_day=settings.get("max_articles_per_day", 15))
    news_summary = summarize.summarize_articles(articles)
    news_html = compose.build_news_html(news_summary, articles)

    print("4/6 - Compongo e invio l'email...")
    full_html = compose.build_full_email_html(
        sections_html=[science_html, reading_html, philosophy_html, german_html, coding_html, poker_html],
        news_html=news_html,
    )
    send_email.send_email(subject=f"Il tuo percorso di oggi — {date.today().isoformat()}", html_content=full_html)

    print("5/6 - Salvo lo stato e aggiorno il log settimanale...")
    day_entry = {
        "science": science_log,
        "reading": reading_log,
        "philosophy": philosophy_log,
        "german": german_log,
        "coding": coding_log,
        "poker": poker_log,
        "feedback_changes": new_feedback_changes,
        "news": {"summary": news_summary, "articles": articles},
    }
    compose.append_to_weekly_log(day_entry)
    state_module.save_state(curriculum_state)

    today_name = date.today().strftime("%A")
    weekly_report_day = settings.get("weekly_report_day", "Sunday")
    if today_name == weekly_report_day:
        print("6/6 - Oggi è il giorno del resoconto: lo genero...")
        report_path = weekly_report.build_weekly_report()
        print(f"   Resoconto salvato in: {report_path}")
    else:
        print("6/6 - Oggi non è il giorno del resoconto settimanale, salto questo passaggio.")

    print("Fatto.")


def _get_env(name):
    import os
    return os.environ[name]


if __name__ == "__main__":
    main()
