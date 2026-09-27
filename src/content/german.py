"""
content/german.py
-------------------
Sezione 4: German. Percorso continuo in blocchi da 5 giorni:
1 introduzione, 2 esercizio, 3 applicazione, 4 esercizio avanzato, 5 test/ripasso.
A differenza di Reading/Philosophy, qui il percorso NON si ferma mai: al
termine di un blocco se ne genera automaticamente uno nuovo (stesso livello,
a meno che tu non lo cambi via feedback).
"""

from llm import generate_text
from content._utils import split_content_and_summary


DAY_STAGES = {
    1: "Introduzione di nuovi contenuti (vocabolario/grammatica)",
    2: "Esercizio pratico sui contenuti introdotti",
    3: "Applicazione in un contesto comunicativo (dialogo, breve testo)",
    4: "Esercizio avanzato/di consolidamento",
    5: "Test e ripasso di tutto il blocco",
}


PROMPT_TEMPLATE = """Sei un tutor di tedesco che scrive in italiano (spiegazioni in italiano,
esempi/esercizi in tedesco con traduzione).

Livello dello studente: {level}
Giorno {day} di {block_length} del blocco corrente. Fase di oggi: {stage}

Cosa è stato trattato nel percorso finora (vuoto se è il primissimo giorno):
{progress_notes}

Scrivi il contenuto di oggi coerente con la fase indicata. Se è un esercizio,
includi 4-6 domande/frasi da tradurre o completare, SENZA le soluzioni nel
corpo principale — aggiungi le soluzioni in una sezione finale ben separata
("Soluzioni"). Se è un test/ripasso, copri i punti chiave del blocco appena
concluso.

Struttura la risposta così:
[contenuto per l'email]

RIEPILOGO_INTERNO: [2-3 frasi su cosa hai coperto oggi e sui progressi generali, per continuità]
"""


def generate_german_section(german_state):
    day = german_state["day_in_block"]

    stage = DAY_STAGES.get(
        day,
        "Ripasso",
    )

    prompt = PROMPT_TEMPLATE.format(
        level=german_state["level"],
        day=day,
        block_length=german_state["block_length"],
        stage=stage,
        progress_notes=german_state.get("progress_notes")
        or "(primo giorno)",
    )

    raw = generate_text(prompt)
    content, summary = split_content_and_summary(raw)

    log_entry = {
        "text": f"[{stage}] {content}"
    }

    german_state["progress_notes"] = (
        summary
        or german_state.get("progress_notes", "")
    )

    # Percorso continuo: dopo l'ultimo giorno del blocco
    # si riparte da 1.
    if day >= german_state["block_length"]:
        german_state["day_in_block"] = 1
    else:
        german_state["day_in_block"] = day + 1

    return content, german_state, log_entry