"""
content/philosophy.py
----------------------
Sezione 3: Philosophy. Un filosofo ogni 5 giorni, con un tema fisso per
ciascun giorno del blocco.
"""

from llm import generate_text
from content._utils import split_content_and_summary

DAY_THEMES = {
    1: "Biografia e contesto storico",
    2: "Contesto filosofico e influenze (chi ha letto/studiato, correnti di riferimento)",
    3: "Il pensiero: concetti e argomentazioni centrali",
    4: "Le opere principali: contenuto e struttura",
    5: "Fortuna, influenza successiva e letture consigliate per approfondire",
}

PROMPT_TEMPLATE = """Sei un tutor di filosofia che scrive in italiano.

Filosofo: {philosopher}
Oggi è il giorno {day} di {block_length} del blocco dedicato a questo filosofo.
Tema di oggi: {theme}

Cosa è stato trattato nei giorni precedenti di questo blocco (vuoto se è il primo giorno):
{progress_notes}

Scrivi un testo chiaro e ben strutturato sul tema di oggi, con esempi concreti
quando utile. Evita di anticipare i temi dei giorni successivi del blocco.

Struttura la risposta così:
[contenuto per l'email]

RIEPILOGO_INTERNO: [2-3 frasi su cosa hai coperto oggi, per continuità]
"""


def generate_philosophy_section(philosophy_state):
    if philosophy_state["day_in_block"] > philosophy_state["block_length"]:
        html = (
            "<h2>3. Philosophy</h2>"
            f"<p><strong>{philosophy_state['philosopher']}</strong> — completato ✅. "
            "Rispondi a questa email con il prossimo filosofo per continuare.</p>"
        )
        return html, philosophy_state, None

    day = philosophy_state["day_in_block"]
    theme = DAY_THEMES.get(day, "Approfondimento")

    prompt = PROMPT_TEMPLATE.format(
        philosopher=philosophy_state["philosopher"],
        day=day,
        block_length=philosophy_state["block_length"],
        theme=theme,
        progress_notes=philosophy_state.get("progress_notes") or "(primo giorno)",
    )
    raw = generate_text(prompt)
    content, summary = split_content_and_summary(raw)

    html = (
        f"<h2>3. Philosophy</h2>"
        f"<h3>{philosophy_state['philosopher']} — giorno {day}/{philosophy_state['block_length']}: {theme}</h3>"
        f"<div>{_to_html_paragraphs(content)}</div>"
    )
    log_entry = {"philosopher": philosophy_state["philosopher"], "day_in_block": day, "text": content}

    philosophy_state["progress_notes"] = summary or philosophy_state.get("progress_notes", "")
    philosophy_state["day_in_block"] += 1
    return html, philosophy_state, log_entry