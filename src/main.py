"""
main.py
-------
Punto di ingresso.

Lunedì–venerdì:
  1. Legge il feedback nuovo dalle risposte email e aggiorna lo stato
  2. Genera il contenuto di oggi per le 6 sezioni del curriculum
  3. Genera la sezione News (RSS)
  4. Genera il PDF giornaliero e lo invia via email
  5. Salva lo stato e registra il giorno nel log settimanale

Sabato:
  6. Genera il resoconto settimanale a partire dal log accumulato
     durante la settimana e lo invia via email

Domenica:
  Nessuna esecuzione.
"""

from copy import deepcopy
from datetime import date

import state as state_module
import feedback
import fetch
import summarize
import send_email
import daily_report
import weekly_report
import compose

from content.science import generate_science_section
from content.reading import generate_reading_section
from content.philosophy import generate_philosophy_section
from content.german import generate_german_section
from content.coding import generate_coding_section
from content.poker import generate_poker_section


def main():
    today = date.today()
    weekday = today.weekday()

    # ------------------------------------------------------------------
    # DOMENICA
    # ------------------------------------------------------------------
    # Python:
    # Monday    = 0
    # Tuesday   = 1
    # Wednesday = 2
    # Thursday  = 3
    # Friday    = 4
    # Saturday  = 5
    # Sunday    = 6

    if weekday == 6:
        print("Oggi è domenica: nessuna esecuzione prevista.")
        return

    # ------------------------------------------------------------------
    # SABATO — WEEKLY REPORT
    # ------------------------------------------------------------------

    if weekday == 5:
        print(
            "Oggi è sabato: genero il resoconto settimanale..."
        )

        try:
            report_path = weekly_report.build_weekly_report()

            if report_path:
                send_email.send_email(
                    subject=(
                        "Resoconto settimanale — "
                        f"{today.isoformat()}"
                    ),
                    body="",
                    attachment_path=report_path,
                )

                print(
                    f"✓ Resoconto settimanale inviato: "
                    f"{report_path}"
                )

            else:
                print(
                    "Nessun resoconto settimanale da generare."
                )

        except Exception as e:
            print(
                f"⚠ Resoconto settimanale fallito: "
                f"{type(e).__name__}: {e}"
            )

            # Il weekly report è l'operazione principale del sabato.
            # Facciamo fallire il job per rendere evidente l'errore
            # a GitHub Actions.
            raise

        print("Fatto.")
        return

    # ------------------------------------------------------------------
    # LUNEDÌ–VENERDÌ
    # ------------------------------------------------------------------

    # Questo è il numero del giorno della settimana:
    #
    # Monday    -> 1
    # Tuesday   -> 2
    # Wednesday -> 3
    # Thursday  -> 4
    # Friday    -> 5
    #
    # Al momento non viene passato ai generatori perché ciascun
    # percorso mantiene il proprio stato interno. È comunque
    # disponibile qui se servirà in futuro.
    day_number = weekday + 1

    print(
        f"=== Giorno {day_number}/5 "
        f"({today.strftime('%A')}) ==="
    )

    curriculum_state = state_module.load_state()
    failed_steps = []

    # ------------------------------------------------------------------
    # 1. FEEDBACK
    # ------------------------------------------------------------------

    print(
        "1/6 - Controllo il feedback nelle risposte email..."
    )

    recipients = [
        r.strip()
        for r in _get_env("RECIPIENT_EMAIL").split(",")
    ]

    feedback_log_before = len(
        curriculum_state.get("feedback_log", [])
    )

    try:
        curriculum_state = feedback.process_feedback(
            curriculum_state,
            gmail_user=_get_env("GMAIL_USER"),
            gmail_password=_get_env("GMAIL_APP_PASSWORD"),
            allowed_senders=recipients,
        )

    except Exception as e:
        failed_steps.append("Feedback")

        print(
            f"   ⚠ Feedback fallito: "
            f"{type(e).__name__}: {e}"
        )

        print(
            "   Proseguo senza applicare nuove modifiche "
            "dal feedback."
        )

    new_feedback_changes = [
        entry["change"]
        for entry in curriculum_state.get(
            "feedback_log",
            [],
        )[feedback_log_before:]
    ]

    print(
        f"   {len(new_feedback_changes)} "
        "modifiche applicate dal feedback."
    )

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
            "Contenuto non disponibile oggi. "
            "Verrà riprovato domani.",
        ),
        (
            "Reading",
            "reading",
            generate_reading_section,
            "Contenuto non disponibile oggi. "
            "Verrà riprovato domani.",
        ),
        (
            "Philosophy",
            "philosophy",
            generate_philosophy_section,
            "Contenuto non disponibile oggi. "
            "Verrà riprovato domani.",
        ),
        (
            "German",
            "german",
            generate_german_section,
            "Contenuto non disponibile oggi. "
            "Verrà riprovato domani.",
        ),
        (
            "Coding",
            "coding",
            generate_coding_section,
            "Contenuto non disponibile oggi. "
            "Verrà riprovato domani.",
        ),
        (
            "Poker",
            "poker",
            generate_poker_section,
            "Contenuto non disponibile oggi. "
            "Verrà riprovato domani.",
        ),
    ]

    # Contenuto grezzo usato dal PDF giornaliero.
    sections = {}

    # Log usato dal report settimanale.
    section_logs = {}

    for (
        name,
        state_key,
        generator,
        fallback_text,
    ) in section_specs:

        (
            content,
            new_section_state,
            log_entry,
            success,
        ) = _safe_generate_section(
            name=name,
            generator=generator,
            section_state=curriculum_state[state_key],
            fallback_text=fallback_text,
        )

        sections[state_key] = content
        section_logs[state_key] = log_entry

        if success:
            curriculum_state[state_key] = (
                new_section_state
            )
        else:
            failed_steps.append(name)

    # ------------------------------------------------------------------
    # 3. NEWS
    # ------------------------------------------------------------------

    print(
        "3/6 - Genero la sezione News (RSS)..."
    )

    settings = {}
    articles = []

    news_summary = (
        "Sezione News non disponibile oggi. "
        "Verrà riprovata domani."
    )

    try:
        sources, settings = fetch.load_sources()

        articles = fetch.fetch_recent_articles(
            sources,
            max_articles_per_day=settings.get(
                "max_articles_per_day",
                15,
            ),
        )

        print(
            f"   Recuperati {len(articles)} articoli."
        )

    except Exception as e:
        failed_steps.append("News fetch")

        print(
            f"   ⚠ Recupero RSS fallito: "
            f"{type(e).__name__}: {e}"
        )

        articles = []

    if articles:

        try:
            news_summary = summarize.summarize_articles(
                articles
            )

        except Exception as e:
            failed_steps.append("News summarize")

            print(
                f"   ⚠ Sintesi News fallita: "
                f"{type(e).__name__}: {e}"
            )

            news_summary = (
                "La sintesi automatica delle notizie "
                "non è disponibile oggi. "
                "Gli articoli recuperati sono riportati "
                "nel PDF."
            )

    elif "News fetch" not in failed_steps:

        news_summary = (
            "Nessun nuovo articolo rilevante "
            "nelle ultime 24 ore."
        )

    # ------------------------------------------------------------------
    # 4. PDF + EMAIL
    # ------------------------------------------------------------------

    print(
        "4/6 - Genero il PDF giornaliero "
        "e invio l'email..."
    )

    daily_pdf_path = (
        daily_report.build_daily_report(
            sections=sections,
            news_summary=news_summary,
            articles=articles,
            report_date=today,
        )
    )

    send_email.send_email(
        subject=(
            f"Il tuo percorso di oggi — "
            f"{today.isoformat()}"
        ),
        body="",
        attachment_path=daily_pdf_path,
    )

    print(
        f"   ✓ PDF giornaliero inviato: "
        f"{daily_pdf_path}"
    )

    # ------------------------------------------------------------------
    # 5. LOG + STATO
    # ------------------------------------------------------------------

    print(
        "5/6 - Salvo lo stato e aggiorno "
        "il log settimanale..."
    )

    day_entry = {
        "date": today.isoformat(),

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

    compose.append_to_weekly_log(
        day_entry
    )

    state_module.save_state(
        curriculum_state
    )

    # ------------------------------------------------------------------
    # 6. WEEKLY REPORT
    # ------------------------------------------------------------------
    # Il sabato viene gestito all'inizio di main(), quindi qui
    # non dobbiamo generare il weekly report.

    print(
        "6/6 - Weekly report previsto per sabato; "
        "oggi è un giorno feriale."
    )

    # ------------------------------------------------------------------
    # RIEPILOGO
    # ------------------------------------------------------------------

    if failed_steps:

        print()
        print(
            "⚠ Newsletter completata con "
            "alcuni step saltati:"
        )

        for step in failed_steps:
            print(f"   - {step}")

    else:

        print()
        print(
            "✓ Newsletter completata senza errori."
        )

    print("Fatto.")


def _safe_generate_section(
    name,
    generator,
    section_state,
    fallback_text,
):
    """
    Esegue una sezione su una copia dello stato.

    Se il generator fallisce:
      - il programma continua;
      - lo stato originale resta intatto;
      - viene restituito un fallback testuale;
      - il log della sezione viene lasciato vuoto.
    """

    try:
        working_state = deepcopy(
            section_state
        )

        (
            content,
            new_state,
            log_entry,
        ) = generator(
            working_state
        )

        print(
            f"   ✓ {name}"
        )

        return (
            content,
            new_state,
            log_entry,
            True,
        )

    except Exception as e:

        print(
            f"   ⚠ {name} fallita: "
            f"{type(e).__name__}: {e}"
        )

        print(
            f"      {name}: stato NON avanzato, "
            "verrà ritentata domani."
        )

        return (
            fallback_text,
            section_state,
            None,
            False,
        )


def _get_env(name):
    import os

    return os.environ[name]


if __name__ == "__main__":
    main()