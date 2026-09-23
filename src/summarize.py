"""
summarize.py
------------
Genera il riassunto degli articoli usando un modello AI.
Interruttore tramite variabile d'ambiente LLM_PROVIDER:
  - "gemini"  -> usa l'API gratuita di Google Gemini (richiede GEMINI_API_KEY)
  - "ollama"  -> usa un modello locale via Ollama (richiede Ollama installato
                 sul computer che esegue lo script; NON funziona su GitHub Actions)
"""

import os
import requests


PROMPT_TEMPLATE = """Sei un assistente che scrive newsletter in italiano, chiaro e conciso.
Di seguito trovi una lista di articoli (titolo, fonte, breve estratto).
Scrivi un riassunto giornaliero in italiano con questa struttura:

1. Un'introduzione di 1-2 frasi sul tema principale della giornata.
2. Un elenco puntato con un breve riassunto (max 2 frasi) per ogni articolo,
   indicando la fonte tra parentesi.

Non inventare informazioni non presenti negli articoli.

ARTICOLI:
{articles_text}
"""


def summarize_articles(articles):
    """Punto di ingresso unico: sceglie il provider e ritorna il testo del riassunto."""
    if not articles:
        return "Nessun nuovo articolo rilevante nelle ultime 24 ore."

    articles_text = _format_articles_for_prompt(articles)
    prompt = PROMPT_TEMPLATE.format(articles_text=articles_text)

    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()

    if provider == "ollama":
        return _summarize_with_ollama(prompt)
    return _summarize_with_gemini(prompt)


def _format_articles_for_prompt(articles):
    lines = []
    for a in articles:
        lines.append(f"- Titolo: {a['title']}\n  Fonte: {a['source']}\n  Estratto: {a['summary']}")
    return "\n\n".join(lines)


def _summarize_with_gemini(prompt):
    import google.generativeai as genai

    api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")  # modello leggero, incluso nel tier gratuito
    response = model.generate_content(prompt)
    return response.text


def _summarize_with_ollama(prompt):
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    response = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"]
