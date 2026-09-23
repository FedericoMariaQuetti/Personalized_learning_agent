# Newsletter Agent

Agente automatico e gratuito che ogni giorno legge alcune fonti RSS, genera
un riassunto con AI (Gemini, tier gratuito) e lo invia via email. Una volta a
settimana produce un resoconto scaricabile in `reports/`.

Per capire come funziona nel dettaglio: leggi [`docs/ARCHITETTURA.md`](docs/ARCHITETTURA.md).

## Attivazione (5 passaggi)

### 1. Carica questo progetto su GitHub
Crea un nuovo repository (può essere pubblico, così GitHub Actions è
gratuito senza limiti pratici) e carica dentro tutti questi file.

### 2. Ottieni una chiave Gemini gratuita
Vai su https://aistudio.google.com/app/apikey e crea una API key gratuita.

### 3. Crea una "App Password" di Gmail
1. Vai su https://myaccount.google.com/security
2. Attiva la verifica in due passaggi
3. Cerca "Password per le app" e generane una

### 4. Inserisci i Secrets su GitHub
Nel tuo repository: **Settings → Secrets and variables → Actions → New repository secret**.
Crea questi 4 secrets:

| Nome | Valore |
|---|---|
| `GEMINI_API_KEY` | la chiave ottenuta al punto 2 |
| `GMAIL_USER` | il tuo indirizzo Gmail |
| `GMAIL_APP_PASSWORD` | la password ottenuta al punto 3 |
| `RECIPIENT_EMAIL` | indirizzo/i a cui inviare (separati da virgola) |

### 5. Modifica le fonti (facoltativo) e avvia
Apri `config/sources.yaml` e personalizza i feed RSS che vuoi seguire.

Per testare subito senza aspettare le 07:00: vai nella scheda **Actions** del
tuo repository, seleziona "Newsletter giornaliera" e clicca **Run workflow**.

## Struttura del progetto
```
config/sources.yaml     ← fonti RSS e impostazioni (modificabile senza toccare il codice)
src/                     ← codice Python
data/weekly_log.json     ← "diario" della settimana (generato automaticamente)
reports/                 ← resoconti settimanali scaricabili (generati automaticamente)
.github/workflows/       ← automazione GitHub Actions
docs/ARCHITETTURA.md     ← spiegazione dettagliata del funzionamento
```

## Test in locale (facoltativo)
Se vuoi provare lo script sul tuo PC prima di caricarlo:
```bash
pip install -r requirements.txt
cp .env.example .env   # poi compila .env con le tue chiavi
cd src
python main.py
```
