"""
weekly_report.py
----------------
Prende tutte le voci accumulate durante la settimana (data/weekly_log.json)
e genera un unico file markdown scaricabile in reports/, poi svuota il log
per far ripartire la settimana successiva.
"""

import json
import os
from datetime import date

LOG_PATH = "data/weekly_log.json"
REPORTS_DIR = "reports"


def build_weekly_report():
    """Genera il resoconto settimanale in Markdown. Ritorna il path del file creato."""
    if not os.path.exists(LOG_PATH):
        return None

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        log = json.load(f)

    entries = log.get("entries", [])
    if not entries:
        return None

    lines = [f"# Resoconto settimanale — settimana del {entries[0]['date']}\n"]

    for entry in entries:
        lines.append(f"## {entry['date']}\n")
        lines.append(entry["summary"] + "\n")
        lines.append("**Fonti:**\n")
        for a in entry["articles"]:
            lines.append(f"- [{a['title']}]({a['link']}) — {a['source']}")
        lines.append("")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = f"{REPORTS_DIR}/{date.today().isoformat()}_resoconto_settimanale.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Svuota il log per la settimana successiva
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump({"entries": []}, f, ensure_ascii=False, indent=2)

    return filename
