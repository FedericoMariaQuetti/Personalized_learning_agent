"""
content/poker.py
------------------
Sezione 6: Poker theory. Corso continuo di strategia (Federico conosce già
le regole, quindi si parte direttamente dai concetti strategici di base).
"""

from llm import generate_text
from content._utils import split_content_and_summary


PROMPT_TEMPLATE = """Sei un tutor di teoria del poker (Texas Hold'em, salvo diversa indicazione)
che scrive in italiano.

Contesto dello studente: {starting_point}

Cosa è stato trattato finora nel corso (vuoto se è il primo giorno):
{progress_notes}

Scrivi la lezione di oggi, proseguendo in modo organico dal punto in cui il
corso è arrivato (se è il primo giorno, comincia dai concetti strategici più
fondamentali, es. range di apertura, posizione al tavolo). Includi almeno un
esempio pratico concreto (una mano o una situazione tipo). Introduci un solo
concetto principale per email, per non sovraccaricare.

Struttura la risposta così:
[contenuto per l'email]

RIEPILOGO_INTERNO: [2-3 frasi sul concetto coperto oggi, per continuità]
"""


def generate_poker_section(poker_state):
    prompt = PROMPT_TEMPLATE.format(
        starting_point=poker_state["starting_point"],
        progress_notes=poker_state.get("progress_notes")
        or "(primo giorno)",
    )

    raw = generate_text(prompt)
    content, summary = split_content_and_summary(raw)

    log_entry = {
        "text": content
    }

    if summary:
        poker_state["progress_notes"] = (
            poker_state.get("progress_notes", "")
            + "\n"
            + summary
        ).strip()

    poker_state["day_count"] += 1

    return content, poker_state, log_entry
