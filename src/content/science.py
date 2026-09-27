"""
content/science.py
-------------------
Sezione 1: Science. Gestisce fino a 3 argomenti scientifici in parallelo,
ognuno con il proprio ritmo (5/10/20 giorni) e la propria continuità.
"""

from copy import deepcopy

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

    Ogni topic è indipendente:
    se uno fallisce, gli altri vengono comunque generati.

    Ritorna:
        (raw_text, nuovo_stato_science, log_topics)
    """

    content_parts = []
    updated_topics = []
    log_topics = []

    for topic in science_state["topics"]:

        # ---------------------------------------------------------------
        # ARGOMENTO GIÀ CONCLUSO
        # ---------------------------------------------------------------

        if topic["day"] > topic["track_days"]:
            content_parts.append(
                f"{topic['name']} — concluso\n\n"
                "Percorso completato. Rispondi a questa email indicando "
                "un nuovo argomento scientifico per continuare su questo slot."
            )

            updated_topics.append(topic)
            continue

        # ---------------------------------------------------------------
        # LAVORIAMO SU UNA COPIA DEL SINGOLO TOPIC
        # ---------------------------------------------------------------

        topic_working = deepcopy(topic)

        try:
            prompt = PROMPT_TEMPLATE.format(
                name=topic_working["name"],
                day=topic_working["day"],
                track_days=topic_working["track_days"],
                track=topic_working["track"],
                special_instructions=topic_working.get(
                    "special_instructions",
                    "",
                ),
                progress_notes=topic_working.get(
                    "progress_notes"
                ) or "(primo giorno)",
            )

            raw = generate_text(prompt)

            content, summary = split_content_and_summary(raw)

            # -----------------------------------------------------------
            # TESTO GREZZO
            # -----------------------------------------------------------

            topic_header = (
                f"{topic_working['name']} "
                f"(giorno {topic_working['day']}/{topic_working['track_days']})"
            )

            content_parts.append(
                f"{topic_header}\n\n{content}"
            )

            # -----------------------------------------------------------
            # LOG
            # -----------------------------------------------------------

            log_topics.append({
                "name": topic_working["name"],
                "day": topic_working["day"],
                "track_days": topic_working["track_days"],
                "text": content,
            })

            # -----------------------------------------------------------
            # AGGIORNAMENTO STATO
            # -----------------------------------------------------------

            topic_working["progress_notes"] = (
                summary
                or topic_working.get("progress_notes", "")
            )

            topic_working["day"] += 1

            # Commit del topic solo se tutto è andato bene.
            updated_topics.append(topic_working)

            print(
                f"      ✓ Science / {topic['name']}"
            )

        except Exception as e:
            print(
                f"      ⚠ Science / {topic['name']} fallito: "
                f"{type(e).__name__}: {e}"
            )
            print(
                "         Topic invariato: verrà ritentato domani."
            )

            # Manteniamo ESATTAMENTE il topic originale.
            updated_topics.append(topic)

            content_parts.append(
                f"{topic['name']}\n\n"
                "Contenuto non disponibile oggi. "
                "Verrà riprovato domani."
            )

    science_state["topics"] = updated_topics

    return "\n\n".join(content_parts), science_state, log_topics