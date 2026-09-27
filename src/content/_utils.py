"""
_utils.py
---------
Funzione condivisa da tutti i moduli in content/.

Ogni prompt chiede all'AI di terminare la risposta con una riga
"RIEPILOGO_INTERNO: ..." che riassume in 2-3 frasi cosa è stato
trattato oggi. Questo riepilogo NON va nell'email: viene salvato nello
stato e usato il giorno dopo per dare continuità, senza dover rimandare
all'AI tutto il testo dei giorni precedenti (risparmia token e quota).
"""

MARKER = "RIEPILOGO_INTERNO:"


def split_content_and_summary(raw_text):
    """Ritorna (testo_per_email, riepilogo_interno)."""
    if MARKER in raw_text:
        content, _, summary = raw_text.partition(MARKER)
        return content.strip(), summary.strip()
    # Se l'AI dimentica il marcatore, usiamo tutto il testo com'è
    # e lasciamo vuoto il riepilogo (il giorno dopo si perderà un po'
    # di continuità, ma non è un errore bloccante).
    return raw_text.strip(), ""
