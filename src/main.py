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

from copy import deepcopy
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
    failed_steps = []

    # ------------------------------------------------------------------
    # 1. FEEDBACK
    # ------------------------------------------------------------------
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
        failed_steps.append("Feedback")
        print(f"   ⚠ Feedback fallito: {type(e).__name__}: {e}")
        print("   Proseguo senza applicare nuove modifiche dal feedback.")

    new_feedback_changes = [
        entry["change"]
        for entry in curriculum_state.get("feedback_log", [])[feedback_log_before:]
    ]

    print(f"   {len(new_feedback_changes)} modifiche applicate dal feedback.")

    # ------------------------------------------------------------------
    # 2. SEZIONI CURRICULUM
    # ------------------------------------------------------------------
    print(
        "2/6 - Genero le sezioni del curriculum "
        "(Science, Reading, Philosophy, German, Coding, Poker)..."
    )

    section_specs = [
        (
            "Science",
            "science",
            generate_science_section,
            "<h2>1. Science</h2>"
            "<p>Contenuto non disponibile oggi. Verrà riprovato domani.</p>",
        ),
        (
            "Reading",
            "reading",
            generate_reading_section,
            "<h2>2. Reading</h2>"
            "<p>Contenuto non disponibile oggi. Verrà riprovato domani.</p>",
        ),
        (
            "Philosophy",
            "philosophy",
            generate_philosophy_section,
            "<h2>3. Philosophy</h2>"
            "<p>Contenuto non disponibile oggi. Verrà riprovato domani.</p>",
        ),
        (
            "German",
            "german",
            generate_german_section,
            "<h2>4. German</h2>"
            "<p>Contenuto non disponibile oggi. Verrà riprovato domani.</p>",
        ),
        (
            "Coding",
            "coding",
            generate_coding_section,
            "<h2>5. Coding</h2>"
            "<p>Contenuto non disponibile oggi. Verrà riprovato domani.</p>",
        ),
        (
            "Poker",
            "poker",
            generate_poker_section,
            "<h2>6. Poker theory</h2>"
            "<p>Contenuto non disponibile oggi. Verrà riprovato domani.</p>",
        ),
    ]

    sections_html = []
    section_logs = {}

    for name, state_key, generator, fallback_html in section_specs:
        html, new_section_state, log_entry, success = _safe_generate_section(
            name=name,
            generator=generator,
            section_state=curriculum_state[state_key],
            fallback_html=fallback_html,
        )

        sections_html.append(html)
        section_logs[state_key] = log_entry

        if success:
            # Assegno lo stato SOLO dopo una generazione completata.
            curriculum_state[state_key] = new_section_state
        else:
            failed_steps.append(name)

    # ------------------------------------------------------------------
    # 3. NEWS
    # ------------------------------------------------------------------
    print("3/6 - Genero la sezione News (RSS)...")

    settings = {}
    articles = []
    news_summary = "Sezione News non disponibile oggi. Verrà riprovata domani."

    try:
        sources, settings = fetch.load_sources()
        articles = fetch.fetch_recent_articles(
            sources,
            max_articles_per_day=settings.get("max_articles_per_day", 15),
        )
        print(f"   Recuperati {len(articles)} articoli.")
    except Exception as e:
        failed_steps.append("News fetch")
        print(f"   ⚠ Recupero RSS fallito: {type(e).__name__}: {e}")
        articles = []

    if articles:
        try:
            news_summary = summarize.summarize_articles(articles)
        except Exception as e:
            failed_steps.append("News summarize")
            print(f"   ⚠ Sintesi News fallita: {type(e).__name__}: {e}")

            # Se la sintesi AI fallisce, almeno manteniamo la lista degli articoli.
            news_summary = (
                "La sintesi automatica delle notizie non è disponibile oggi. "
                "Gli articoli recuperati sono riportati qui sotto."
            )
    elif not failed_steps or "News fetch" not in failed_steps:
        news_summary = "Nessun nuovo articolo rilevante nelle ultime 24 ore."

    news_html = compose.build_news_html(news_summary, articles)

    # ------------------------------------------------------------------
    # 4. COMPOSIZIONE E INVIO
    # ------------------------------------------------------------------
    print("4/6 - Compongo e invio l'email...")

    full_html = compose.build_full_email_html(
        sections_html=sections_html,
        news_html=news_html,
    )

    # Questo NON viene nascosto: se l'email fallisce, il job deve fallire.
    send_email.send_email(
        subject=f"Il tuo percorso di oggi — {date.today().isoformat()}",
        html_content=full_html,
    )

    # ------------------------------------------------------------------
    # 5. LOG + STATO
    # ------------------------------------------------------------------
    print("5/6 - Salvo lo stato e aggiorno il log settimanale...")

    day_entry = {
        "science": section_logs["science"],
        "reading": section_logs["reading"],
        "philosophy": section_logs["philosophy"],
        "german": section_logs["german"],
        "coding": section_logs["coding"],
        "poker": section_logs["poker"],
        "feedback_changes": new_feedback_changes,
        "news": {
            "summary": news_summary,
            "articles": articles,
        },
    }

    compose.append_to_weekly_log(day_entry)
    state_module.save_state(curriculum_state)

    # ------------------------------------------------------------------
    # 6. WEEKLY REPORT
    # ------------------------------------------------------------------
    today_name = date.today().strftime("%A")
    weekly_report_day = settings.get("weekly_report_day", "Sunday")

    if today_name == weekly_report_day:
        print("6/6 - Oggi è il giorno del resoconto: lo genero...")

        try:
            report_path = weekly_report.build_weekly_report()

            if report_path:
                print(f"   Resoconto salvato in: {report_path}")
            else:
                print("   Nessun resoconto da generare.")
        except Exception as e:
            failed_steps.append("Weekly report")
            print(f"   ⚠ Resoconto settimanale fallito: {type(e).__name__}: {e}")
    else:
        print(
            "6/6 - Oggi non è il giorno del resoconto settimanale, "
            "salto questo passaggio."
        )

    # ------------------------------------------------------------------
    # RIEPILOGO
    # ------------------------------------------------------------------
    if failed_steps:
        print()
        print("⚠ Newsletter completata con alcuni step saltati:")
        for step in failed_steps:
            print(f"   - {step}")
    else:
        print()
        print("✓ Newsletter completata senza errori.")

    print("Fatto.")


def _safe_generate_section(name, generator, section_state, fallback_html):
    """
    Esegue una sezione su una copia dello stato.

    Se il generator fallisce:
      - il programma continua;
      - lo stato originale resta intatto;
      - viene restituito un fallback HTML;
      - il log della sezione viene lasciato vuoto.
    """
    try:
        working_state = deepcopy(section_state)
        html, new_state, log_entry = generator(working_state)

        print(f"   ✓ {name}")
        return html, new_state, log_entry, True

    except Exception as e:
        print(f"   ⚠ {name} fallita: {type(e).__name__}: {e}")
        print(f"      {name}: stato NON avanzato, verrà ritentata domani.")
        return fallback_html, section_state, None, False


def _get_env(name):
    import os
    return os.environ[name]


if __name__ == "__main__":
    main()