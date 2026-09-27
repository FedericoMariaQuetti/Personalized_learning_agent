"""
content/science.py
-------------------
Sezione 1: Science. Gestisce fino a 3 argomenti scientifici in parallelo,
ognuno con il proprio ritmo (5/10/20 giorni) e la propria continuità.
"""

from llm import generate_text
from content._utils import split_content_and_summary

PROMPT_TEMPLATE = """Sei un tutor scientifico che scrive in italiano per uno studente universitario
con solide basi di programmazione e statistica.

Argomento di oggi: "{name}"
Percorso: giorno {day} di {track_days} (ritmo "{track}").
{special_instructions}

Cosa è stato trattato finora su questo argomento (vuoto se è il primo giorno):
{progress_notes}

Istruzioni per il contenuto di oggi:
- Massimo 500 parole.
- Usa Wikipedia in inglese come mappa concettuale iniziale, poi integra con
  letteratura scientifica più approfondita (manuali, paper, risultati noti).
- Includi formule o pseudo-codice/algoritmi quando utili alla comprensione.
- Cita 2-3 riferimenti (nome autore/opera o link) alla fine.
- Non ripetere quanto già trattato nei giorni precedenti: prosegui da lì.
- Se questo è l'ultimo giorno del percorso (giorno {day} di {track_days}), chiudi
  con una sintesi complessiva dell'argomento.

Struttura la risposta così:
[contenuto per l'email]

RIEPILOGO_INTERNO: [2-3 frasi su cosa hai coperto oggi, per dare continuità domani]
"""


def generate_science_section(science_state):
    """
    Genera il contenuto di oggi per tutti gli argomenti attivi.
    Ritorna (html_snippet, nuovo_stato_science, log_topics) dove log_topics è
    una lista di {"name", "day", "track_days", "text"} per il resoconto settimanale.
    """
    html_parts = ["<h2>1. Science</h2>"]
    updated_topics = []
    log_topics = []

    for topic in science_state["topics"]:
        if topic["day"] > topic["track_days"]:
            # Argomento concluso: aspetta un nuovo argomento via feedback
            html_parts.append(
                f"<h3>{topic['name']} — concluso ✅</h3>"
                f"<p>Percorso completato. Rispondi a questa email indicando un nuovo "
                f"argomento scientifico per continuare su questo slot.</p>"
            )
            updated_topics.append(topic)
            continue

        prompt = PROMPT_TEMPLATE.format(
            name=topic["name"],
            day=topic["day"],
            track_days=topic["track_days"],
            track=topic["track"],
            special_instructions=topic.get("special_instructions", ""),
            progress_notes=topic.get("progress_notes") or "(primo giorno)",
        )
        raw = generate_text(prompt)
        content, summary = split_content_and_summary(raw)

        html_parts.append(f"<h3>{topic['name']} (giorno {topic['day']}/{topic['track_days']})</h3>")
        html_parts.append(f"<div>{_to_html_paragraphs(content)}</div>")
        log_topics.append({
            "name": topic["name"], "day": topic["day"],
            "track_days": topic["track_days"], "text": content,
        })

        topic["progress_notes"] = summary or topic.get("progress_notes", "")
        topic["day"] += 1
        updated_topics.append(topic)

    science_state["topics"] = updated_topics
    return "\n".join(html_parts), science_state, log_topics


def _to_html_paragraphs(text):
    """Trasforma il testo in paragrafi HTML semplici, mantenendo gli a-capo."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>" for p in paragraphs)
