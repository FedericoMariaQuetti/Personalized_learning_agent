"""
main.py
-------
Punto di ingresso dello script. Ogni giorno esegue in ordine:
  1. Scarica gli articoli nuovi
  2. Genera il riassunto AI
  3. Compone e invia l'email giornaliera
  4. Aggiorna il log settimanale
  5. Se è il giorno impostato (default: domenica), genera il resoconto
     settimanale e lo salva in reports/
"""

from datetime import date

from fetch import load_sources, fetch_recent_articles
from summarize import summarize_articles
from compose import build_daily_email_html, append_to_weekly_log
from send_email import send_email
from weekly_report import build_weekly_report


def main():
    sources, settings = load_sources()
    max_per_day = settings.get("max_articles_per_day", 15)
    weekly_report_day = settings.get("weekly_report_day", "Sunday")

    print("1/5 - Scarico gli articoli recenti...")
    articles = fetch_recent_articles(sources, max_articles_per_day=max_per_day)
    print(f"   Trovati {len(articles)} articoli nuovi.")

    print("2/5 - Genero il riassunto AI...")
    summary_text = summarize_articles(articles)

    print("3/5 - Compongo e invio l'email...")
    html = build_daily_email_html(summary_text, articles)
    send_email(subject=f"Newsletter del {date.today().isoformat()}", html_content=html)

    print("4/5 - Aggiorno il log settimanale...")
    append_to_weekly_log(summary_text, articles)

    today_name = date.today().strftime("%A")  # es. "Sunday"
    if today_name == weekly_report_day:
        print("5/5 - Oggi è il giorno del resoconto: lo genero...")
        report_path = build_weekly_report()
        print(f"   Resoconto salvato in: {report_path}")
    else:
        print("5/5 - Oggi non è il giorno del resoconto settimanale, salto questo passaggio.")

    print("Fatto.")


if __name__ == "__main__":
    main()
