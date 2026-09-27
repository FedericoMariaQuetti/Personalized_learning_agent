"""
summarize.py
------------
Genera il riassunto delle notizie RSS per la sezione "News" (8/8).
Usa il modulo condiviso llm.py per parlare con l'AI.
"""

PROMPT_TEMPLATE = """Sei un assistente che scrive newsletter in italiano, chiaro e conciso.
Di seguito trovi una lista di articoli (titolo, fonte, breve estratto).
Scrivi un riassunto giornaliero in italiano con questa struttura:

1. Un'introduzione di 1-2 frasi sul tema principale della giornata.
2. Un elenco puntato con un breve riassunto (3 frasi) per ogni articolo,
   indicando la fonte tra parentesi.

Non inventare informazioni non presenti negli articoli.

ARTICOLI:
{articles_text}
"""


def summarize_articles(articles):
    from llm import generate_text

    if not articles:
        return "Nessun nuovo articolo rilevante nelle ultime 24 ore."

    articles_text = _format_articles_for_prompt(articles)
    prompt = PROMPT_TEMPLATE.format(articles_text=articles_text)
    return generate_text(prompt)


def _format_articles_for_prompt(articles):
    lines = []
    for a in articles:
        lines.append(f"- Titolo: {a['title']}\n  Fonte: {a['source']}\n  Estratto: {a['summary']}")
    return "\n\n".join(lines)
