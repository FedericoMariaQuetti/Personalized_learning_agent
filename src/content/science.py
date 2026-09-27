"""
content/science.py
-------------------
Sezione 1: Science. Gestisce fino a 3 argomenti scientifici in parallelo,
ognuno con il proprio ritmo (5/10/20 giorni) e la propria continuità.
"""

from copy import deepcopy
from llm import generate_text
from content._utils import split_content_and_summary
from math_render import replace_latex

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

    Ogni topic è indipendente:
    se uno fallisce, gli altri vengono comunque generati.

    Ritorna:
        (html_snippet, nuovo_stato_science, log_topics)
    """
    html_parts = ["<h2>1. Science</h2>"]
    updated_topics = []
    log_topics = []

    for topic in science_state["topics"]:
        # Argomento già concluso: nessuna chiamata LLM.
        if topic["day"] > topic["track_days"]:
            html_parts.append(
                f"<h3>{topic['name']} — concluso ✅</h3>"
                f"<p>Percorso completato. Rispondi a questa email indicando un nuovo "
                f"argomento scientifico per continuare su questo slot.</p>"
            )
            updated_topics.append(topic)
            continue

        # Lavoriamo su una copia del singolo topic.
        topic_working = deepcopy(topic)

        try:
            prompt = PROMPT_TEMPLATE.format(
                name=topic_working["name"],
                day=topic_working["day"],
                track_days=topic_working["track_days"],
                track=topic_working["track"],
                special_instructions=topic_working.get("special_instructions", ""),
                progress_notes=topic_working.get("progress_notes") or "(primo giorno)",
            )

            raw = generate_text(prompt)
            content, summary = split_content_and_summary(raw)

            html_parts.append(
                f"<h3>{topic_working['name']} "
                f"(giorno {topic_working['day']}/{topic_working['track_days']})</h3>"
            )
            html_parts.append(
                f"<div>{_to_html_paragraphs(content)}</div>"
            )

            log_topics.append({
                "name": topic_working["name"],
                "day": topic_working["day"],
                "track_days": topic_working["track_days"],
                "text": content,
            })

            topic_working["progress_notes"] = (
                summary or topic_working.get("progress_notes", "")
            )
            topic_working["day"] += 1

            # Commit del topic solo se tutto è andato bene.
            updated_topics.append(topic_working)

            print(f"      ✓ Science / {topic['name']}")

        except Exception as e:
            print(
                f"      ⚠ Science / {topic['name']} fallito: "
                f"{type(e).__name__}: {e}"
            )
            print("         Topic invariato: verrà ritentato domani.")

            # Manteniamo ESATTAMENTE il topic originale.
            updated_topics.append(topic)

            html_parts.append(
                f"<h3>{topic['name']}</h3>"
                "<p>Contenuto non disponibile oggi. "
                "Verrà riprovato domani.</p>"
            )

    science_state["topics"] = updated_topics

    return "\n".join(html_parts), science_state, log_topics


def _to_html_paragraphs(text):
    """Trasforma il testo scientifico in immagine della formula."""
    text = replace_latex(text)
    """Trasforma il testo in paragrafi HTML semplici, mantenendo gli a-capo."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>" for p in paragraphs)
