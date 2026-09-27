"""
weekly_report.py
----------------
Genera il resoconto settimanale in Markdown a partire dal log accumulato
durante la settimana (data/weekly_log.json), poi svuota il log.
"""

import json
import os
from datetime import date

LOG_PATH = "data/weekly_log.json"
REPORTS_DIR = "reports"


def build_weekly_report():
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

        if entry.get("science"):
            lines.append("### 1. Science")
            for topic in entry["science"]:
                lines.append(f"**{topic['name']}** (giorno {topic['day']}/{topic['track_days']})\n")
                lines.append(topic["text"] + "\n")

        if entry.get("reading"):
            lines.append("### 2. Reading")
            lines.append(f"**{entry['reading']['book']}** (blocco {entry['reading']['day_in_block']})\n")
            lines.append(entry["reading"]["text"] + "\n")

        if entry.get("philosophy"):
            lines.append("### 3. Philosophy")
            lines.append(f"**{entry['philosophy']['philosopher']}** (giorno {entry['philosophy']['day_in_block']})\n")
            lines.append(entry["philosophy"]["text"] + "\n")

        if entry.get("german"):
            lines.append("### 4. German")
            lines.append(entry["german"]["text"] + "\n")

        if entry.get("coding"):
            lines.append("### 5. Coding")
            lines.append(entry["coding"]["text"] + "\n")

        if entry.get("poker"):
            lines.append("### 6. Poker theory")
            lines.append(entry["poker"]["text"] + "\n")

        if entry.get("feedback_changes"):
            lines.append("### 7. Feedback applicato")
            for change in entry["feedback_changes"]:
                lines.append(f"- {change}")
            lines.append("")

        if entry.get("news"):
            lines.append("### 8. News")
            lines.append(entry["news"]["summary"] + "\n")
            for a in entry["news"]["articles"]:
                lines.append(f"- [{a['title']}]({a['link']}) — {a['source']}")
            lines.append("")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = f"{REPORTS_DIR}/{date.today().isoformat()}_resoconto_settimanale.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump({"entries": []}, f, ensure_ascii=False, indent=2)

    return filename
