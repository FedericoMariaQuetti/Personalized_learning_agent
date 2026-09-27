"""
content/coding.py
-----------------
Sezione 5: Coding. Un esercizio Python al giorno, difficoltà a rotazione
(facile/media/difficile), con soluzione e spiegazione nella STESSA email
(scelta di Federico).
"""

from llm import generate_text
from content._utils import split_content_and_summary


PROMPT_TEMPLATE = """Sei un tutor di programmazione Python che scrive in italiano, per uno
studente con basi note (closures, funzioni di ordine superiore, regex,
comprehension, unpacking, functools).

Difficoltà di oggi: {difficulty}

Esercizi/argomenti già proposti in passato, per non ripetersi (vuoto se è il
primo giorno):

{progress_notes}

Scrivi:

1. Un esercizio Python nuovo (mai proposto prima), di difficoltà {difficulty},
   con una consegna chiara.

2. Una soluzione completa e funzionante in un blocco di codice.

3. Una spiegazione dei costrutti Python usati nella soluzione e perché sono
   stati scelti.

Struttura la risposta così:

[contenuto per l'email, con blocchi di codice tra triple backtick]

RIEPILOGO_INTERNO: [una riga che descrive l'argomento/costrutto dell'esercizio di oggi, per non ripeterlo]
"""


def generate_coding_section(coding_state):
    cycle = coding_state["difficulty_cycle"]
    difficulty = cycle[(coding_state["day_count"] - 1) % len(cycle)]

    prompt = PROMPT_TEMPLATE.format(
        difficulty=difficulty,
        progress_notes=coding_state.get("progress_notes") or "(primo giorno)",
    )

    raw = generate_text(prompt)
    content, summary = split_content_and_summary(raw)

    # Il contenuto rimane testo grezzo/Markdown.
    # I blocchi ```...``` verranno formattati dal renderer PDF.
    log_entry = {
        "text": f"[Difficoltà: {difficulty}]\n\n{content}"
    }

    if summary:
        coding_state["progress_notes"] = (
            coding_state.get("progress_notes", "") + "\n" + summary
        ).strip()

    coding_state["day_count"] += 1

    return content, coding_state, log_entry