# Come funziona questo progetto — spiegazione semplice

## L'idea in una frase
Ogni giorno ricevi un'email con 8 sezioni di studio personalizzate. Il
sistema si "ricorda" dove sei arrivato in ognuna, e impara dalle tue
risposte via email per adattare il percorso nel tempo.

## Le 8 sezioni

1. **Science** — fino a 3 argomenti scientifici insieme, ognuno con il suo
   ritmo (5 giorni = intro breve, 10 = intro completa, 20 = rassegna media).
2. **Reading** — un libro ogni 5 giorni, diviso in 5 blocchi narrativi.
3. **Philosophy** — un filosofo ogni 5 giorni (biografia → contesto →
   pensiero → opere → eredità, un tema fisso al giorno).
4. **German** — percorso continuo in blocchi da 5 giorni che si ripetono
   (introduzione, esercizio, applicazione, esercizio avanzato, test/ripasso).
5. **Coding** — un esercizio Python al giorno, difficoltà a rotazione
   (facile/media/difficile), soluzione inclusa nella stessa email.
6. **Poker theory** — corso continuo di strategia, un concetto alla volta.
7. **Feedback** — una sezione fissa che ti ricorda: rispondi a questa email
   per cambiare argomenti, alzare/abbassare la difficoltà, registrare le tue
   risposte agli esercizi, o correggere il percorso.
8. **News** — il vecchio riassunto RSS (tecnologia/attualità), tenuto in coda.

## Il pezzo chiave: `data/curriculum_state.json`

Questo file è la "memoria" del sistema. Contiene, per ogni sezione, a che
punto sei (che giorno del blocco, quale libro/filosofo/argomento) e un breve
"riepilogo dei progressi" scritto dall'AI stessa alla fine di ogni giorno.

Perché un riepilogo e non tutta la cronologia? Perché mandare all'AI *tutto*
quello che hai già letto, ogni giorno, consumerebbe rapidamente la quota
gratuita. Il riepilogo di 2-3 frasi dà continuità senza sprecare risorse.

**Importante**: questo file viene aggiornato automaticamente ad ogni
esecuzione e ricommittato nel repository da GitHub Actions. Non modificarlo
a mano mentre il workflow è attivo, altrimenti rischi conflitti.

## Come funziona il feedback (rispondere all'email)

1. Ogni giorno, PRIMA di generare i contenuti, lo script si collega alla tua
   casella Gmail (in lettura, via IMAP) e cerca tue risposte non lette alla
   newsletter.
2. Se trova qualcosa, manda il testo all'AI chiedendo di restituire un
   elenco preciso di "cosa cambiare" in formato strutturato (JSON) — non
   testo libero.
3. Lo script applica SOLO le modifiche a campi che riconosce (es. "nuovo
   libro", "nuovo argomento scientifico", "nota per il tutor di coding").
   Qualsiasi altra cosa scritta nel JSON che non corrisponde a un campo noto
   viene ignorata: questo evita che un'interpretazione sbagliata rompa lo
   stato.
4. Ogni modifica applicata finisce anche in `feedback_log` dentro lo stato,
   e viene mostrata nel resoconto settimanale — così puoi sempre controllare
   cosa ha "deciso" il sistema.

**Limite onesto**: l'interpretazione del feedback dipende dalla qualità con
cui l'AI capisce il tuo messaggio. Per richieste importanti, scrivi in modo
diretto ("cambia l'argomento di Fisher information in: teoria dei giochi,
ritmo breve") invece che in modo implicito.

## Perché alcune sezioni "si fermano"

Reading, Philosophy e i singoli argomenti di Science hanno una durata
definita. Quando finiscono, il sistema NON sceglie da solo cosa fare dopo:
mostra un messaggio "concluso ✅" e aspetta che tu risponda con il prossimo
libro/filosofo/argomento. German, Coding e Poker invece sono pensati come
percorsi continui e non si fermano mai da soli.

## Struttura del codice

```
src/
├── llm.py                 ← unico punto che parla con Gemini/Ollama
├── state.py                ← legge/scrive data/curriculum_state.json
├── fetch.py, summarize.py  ← sezione News (RSS), invariati da prima
├── compose.py               ← assembla l'email con le 8 sezioni
├── send_email.py            ← invio via Gmail SMTP
├── weekly_report.py          ← genera il resoconto settimanale scaricabile
├── feedback.py               ← legge/interpreta/applica le tue risposte email
├── content/
│   ├── science.py
│   ├── reading.py
│   ├── philosophy.py
│   ├── german.py
│   ├── coding.py
│   └── poker.py             ← un modulo per sezione, ognuno "sa" solo la sua logica
└── main.py                    ← orchestra tutto, in ordine
```

## Cosa resta gratuito
Tutto come prima: GitHub Actions (repo pubblico), Gemini tier gratuito,
Gmail per invio E ora anche per lettura (IMAP è incluso, nessun costo
aggiuntivo, nessun nuovo secret da configurare).

## Se un giorno Gemini smette di funzionare
Il modello è definito in UN SOLO punto: `src/llm.py`, variabile
`GEMINI_MODEL`. Se ricevi un errore "model ... is not found", quello è il
punto da aggiornare.
