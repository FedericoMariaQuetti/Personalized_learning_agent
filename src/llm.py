"""
llm.py
------
Punto unico da cui TUTTE le sezioni della newsletter chiamano l'AI.
Così, se un giorno cambia il modello o il provider, si modifica una
sola volta qui invece che in 7 file diversi.

Interruttore tramite LLM_PROVIDER: "gemini" (default) oppure "ollama".
"""

import os
import requests

# Modello gratuito e stabile consigliato da Google per nuovi progetti (settembre 2026).
# Se in futuro Google lo dismette, questo è l'UNICO punto da aggiornare.
GEMINI_MODEL = "gemini-3.5-flash-lite"


def generate_text(prompt, json_mode=False):
    """
    Genera testo a partire da un prompt.
    Se json_mode=True, chiede al modello di rispondere SOLO con un oggetto JSON
    (usato dal modulo feedback.py per interpretare le tue risposte email).
    """
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()

    if provider == "ollama":
        return _generate_with_ollama(prompt)
    return _generate_with_gemini(prompt, json_mode=json_mode)


def _generate_with_gemini(prompt, json_mode=False):
    import google.generativeai as genai

    api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    generation_config = {"response_mime_type": "application/json"} if json_mode else None
    model = genai.GenerativeModel(GEMINI_MODEL, generation_config=generation_config)
    response = model.generate_content(prompt, request_options={"timeout": 90})
    return response.text


def _generate_with_ollama(prompt):
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    response = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["response"]
