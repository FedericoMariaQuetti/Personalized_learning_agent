# Personal Tutor Newsletter

Agente automatico e gratuito che ogni giorno ti manda un'email con 8 sezioni
di studio personalizzate (Science, Reading, Philosophy, German, Coding,
Poker theory, Feedback, News), si ricorda a che punto sei arrivato, e impara
dalle tue risposte via email.

Per capire come funziona nel dettaglio: leggi [`docs/ARCHITETTURA.md`](docs/ARCHITETTURA.md).

## Attivazione

Se hai già configurato i secrets per la versione precedente (RSS-only), **non
serve rifare nulla**: usa esattamente le stesse 4 chiavi. Il feedback via
email usa lo stesso account Gmail già configurato (lettura IMAP inclusa,
nessun secret aggiuntivo).

Se parti da zero, segui questi passaggi:

### 1. Carica questo progetto su GitHub
Sostituisci tutto il contenuto del tuo repository con questi file (o crealo
da zero se non l'hai ancora fatto).

### 2. Ottieni una chiave Gemini gratuita
https://aistudio.google.com/app/apikey → "Create API key".

### 3. Crea una "App Password" di Gmail
1. https://myaccount.google.com/security → attiva la verifica in due passaggi
2. Cerca "Password per le app" e creane una

### 4. Inserisci i Secrets su GitHub
Settings → Secrets and variables → Actions → New repository secret:

| Nome | Valore |
|---|---|
| `GEMINI_API_KEY` | la chiave del punto 2 |
| `GMAIL_USER` | il tuo indirizzo Gmail |
| `GMAIL_APP_PASSWORD` | la password del punto 3 |
| `RECIPIENT_EMAIL` | il tuo indirizzo (quello da cui risponderai) |

**Importante**: `RECIPIENT_EMAIL` deve essere l'indirizzo esatto da cui
rispondi alle email — il sistema lo usa anche per riconoscere le tue
risposte come feedback valido (ignora tutte le altre email non lette nella
casella).

### 5. Personalizza il punto di partenza (facoltativo)
Il file `data/curriculum_state.json` contiene già i tuoi argomenti di
partenza (Fisher information, distribuzioni in finanza, architetture AI,
I fratelli Karamazov, Heidegger, tedesco A1, poker da livello strategico).
Puoi modificarlo a mano prima del primo invio se vuoi cambiare qualcosa.

### 6. Avvia il primo test
Tab **Actions** → "Newsletter giornaliera" → **Run workflow**.

## Come dare feedback
Rispondi semplicemente all'email ricevuta. Esempi di frasi che il sistema
capisce bene:
- "Cambia l'argomento di [nome] con: teoria dei giochi, ritmo breve"
- "Il libro attuale non mi convince, passiamo a [nuovo libro]"
- "Alza un po' la difficoltà degli esercizi Python"
- "Il mio tedesco è più avanti di A1, direi A2"

Le modifiche applicate compaiono anche nel resoconto settimanale, così puoi
sempre verificare cosa ha capito il sistema.

## Struttura del progetto
```
config/sources.yaml       ← fonti RSS per la sezione News
data/curriculum_state.json ← stato del tuo percorso (si aggiorna da solo)
data/weekly_log.json       ← accumulo dei contenuti della settimana
reports/                    ← resoconti settimanali scaricabili
src/                         ← codice Python (vedi docs/ARCHITETTURA.md)
.github/workflows/            ← automazione GitHub Actions
```

## Test in locale (facoltativo)
```bash
pip install -r requirements.txt
cp .env.example .env   # poi compila .env con le tue chiavi
cd src
python main.py
```
