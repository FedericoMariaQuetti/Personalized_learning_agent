# Come funziona questo progetto — spiegazione semplice

## L'idea in una frase
Ogni giorno, un robot (in realtà è solo uno script Python) legge alcuni siti,
chiede a un'intelligenza artificiale gratuita di riassumerli, e ti manda una
mail. Una volta a settimana, mette insieme tutti i riassunti della settimana
in un file scaricabile dal repository GitHub.

## Chi fa girare lo script?
Non serve un computer sempre acceso: usiamo **GitHub Actions**, un servizio
gratuito di GitHub che accende un piccolo computer virtuale ogni giorno
all'ora che vuoi, esegue lo script, e poi lo spegne. Tutto tracciato nella
scheda "Actions" del tuo repository.

## Il percorso di ogni esecuzione giornaliera

1. **`fetch.py`** — Va a leggere i feed RSS elencati in `config/sources.yaml`
   e prende solo gli articoli pubblicati nelle ultime 24 ore.
2. **`summarize.py`** — Manda gli articoli trovati a Gemini (l'AI gratuita di
   Google) e chiede un riassunto in italiano.
3. **`compose.py`** — Prepara il testo dell'email e salva anche una copia dei
   contenuti di oggi in `data/weekly_log.json` (un "diario" della settimana).
4. **`send_email.py`** — Manda l'email tramite il tuo account Gmail.
5. **`weekly_report.py`** — Solo nel giorno che hai scelto (default: domenica),
   legge tutto il "diario" della settimana e crea un file
   `reports/AAAA-MM-GG_resoconto_settimanale.md`, poi svuota il diario per
   ricominciare la settimana dopo.

## Dove sono le chiavi/password?
Mai scritte nel codice. Vivono come **"Secrets"** nelle impostazioni del tuo
repository GitHub (Settings → Secrets and variables → Actions). Lo script le
legge al momento dell'esecuzione, ma nessuno può vederle guardando il codice.

## Perché è gratuito?
- **GitHub Actions**: gratuito per repository pubblici (con limiti generosi
  che un'esecuzione giornaliera di pochi minuti non raggiunge mai).
- **Gemini**: Google offre un tier gratuito con un numero di richieste al
  giorno più che sufficiente per una newsletter personale.
- **Gmail**: l'invio email tramite il tuo account personale è gratuito fino a
  circa 500 email al giorno.

## E se un giorno voglio usare un'AI locale (Ollama) invece di Gemini?
Il codice è già pronto: basta impostare `LLM_PROVIDER=ollama` invece di
`gemini`. L'unico limite è che Ollama deve girare su un computer con il
modello scaricato — cosa che GitHub Actions non permette facilmente (il
server virtuale si resetta ogni volta). Questa opzione è quindi pensata per
quando vorrai eseguire lo script sul tuo PC invece che su GitHub.

## Cosa puoi modificare senza toccare il codice
Tutto in `config/sources.yaml`:
- Aggiungere/togliere feed RSS
- Cambiare il giorno del resoconto settimanale
- Cambiare quanti articoli processare al massimo al giorno
