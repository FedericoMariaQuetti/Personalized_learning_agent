"""
content/reading.py
-------------------
Sezione 2: Reading. Un libro ogni 5 giorni, suddiviso in 5 blocchi narrativi.
Quando un libro finisce, aspetta il titolo successivo via feedback (oppure
dalla coda "queue" se è già stata popolata).
"""

from llm import generate_text
from content._utils import split_content_and_summary


PROMPT_TEMPLATE = """Sei un tutor di letteratura che scrive in italiano.

Libro: "{book}"
Oggi tratti il blocco narrativo {day} di {block_length} (procedi in ordine
cronologico attraverso il libro, dividendolo in {block_length} parti uguali
in termini di trama).

Cosa è stato trattato nei blocchi precedenti (vuoto se è il primo giorno):
{progress_notes}

Per il blocco di oggi scrivi, in italiano:
1. Riassunto della trama di questa parte del libro.
2. Interpretazione: temi, simbolismo, significato più ampio.
3. Elementi importanti: personaggi chiave, svolte narrative di questa parte.
4. Passaggi significativi: puoi citare direttamente il testo, ma mantieni le
   citazioni brevi e in numero ragionevole (poche righe alla volta, mai
   pagine intere) — l'obiettivo è illustrare, non sostituire la lettura.

Se questo è il blocco 5 di 5, chiudi con una riflessione finale sull'opera
nel suo complesso.

Struttura la risposta così:
[contenuto per l'email]

RIEPILOGO_INTERNO: [2-3 frasi su cosa hai coperto oggi, per continuità]
"""


def generate_reading_section(reading_state):
    if reading_state["day_in_block"] > reading_state["block_length"]:
        content = (
            f"{reading_state['book']} — completato.\n\n"
            "Rispondi a questa email con il titolo del prossimo libro "
            "per continuare."
        )

        return content, reading_state, None

    prompt = PROMPT_TEMPLATE.format(
        book=reading_state["book"],
        day=reading_state["day_in_block"],
        block_length=reading_state["block_length"],
        progress_notes=reading_state.get("progress_notes")
        or "(primo giorno)",
    )

    raw = generate_text(prompt)
    content, summary = split_content_and_summary(raw)

    day_in_block = reading_state["day_in_block"]

    log_entry = {
        "book": reading_state["book"],
        "day_in_block": day_in_block,
        "text": content,
    }

    reading_state["progress_notes"] = (
        summary
        or reading_state.get("progress_notes", "")
    )

    reading_state["day_in_block"] += 1

    return content, reading_state, log_entry

