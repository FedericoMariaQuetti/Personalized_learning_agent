"""
weekly_report.py
----------------
Genera il resoconto settimanale in PDF a partire dal log accumulato
durante la settimana (data/weekly_log.json), organizzato per sezione.

Struttura:

1. Science
   Giorno 1
   Giorno 2
   ...

2. Reading
   Giorno 1
   Giorno 2
   ...

...

7. News

Dopo la generazione corretta del PDF, il log settimanale viene svuotato.
"""

import html
import json
import os
import re
import tempfile
from datetime import date

import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
)


LOG_PATH = "data/weekly_log.json"
REPORTS_DIR = "reports"


# ---------------------------------------------------------------------------
# STILI
# ---------------------------------------------------------------------------

def _get_styles():
    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "WeeklyTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            spaceAfter=18,
        ),
        "section": ParagraphStyle(
            "WeeklySection",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            spaceBefore=16,
            spaceAfter=10,
        ),
        "day": ParagraphStyle(
            "WeeklyDay",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "topic": ParagraphStyle(
            "WeeklyTopic",
            parent=styles["Heading3"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "WeeklyBody",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=15,
            spaceAfter=8,
        ),
        "code": ParagraphStyle(
            "WeeklyCode",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=5,
            spaceAfter=8,
            backColor=colors.whitesmoke,
        ),
        "formula": ParagraphStyle(
            "WeeklyFormula",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            spaceBefore=8,
            spaceAfter=8,
        ),
    }


# ---------------------------------------------------------------------------
# UTILITY TESTO
# ---------------------------------------------------------------------------

def _escape_text(text):
    return html.escape(str(text), quote=False)


def _convert_basic_markdown(text):
    """
    Converte una piccola parte del Markdown in markup ReportLab.
    """

    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text,
    )

    text = re.sub(
        r"(?<!\*)\*([^*\n]+?)\*(?!\*)",
        r"<i>\1</i>",
        text,
    )

    return text


def _text_to_paragraph(text, styles):
    text = _escape_text(text)
    text = _convert_basic_markdown(text)
    text = text.replace("\n", "<br/>")

    return Paragraph(
        text,
        styles["body"],
    )


# ---------------------------------------------------------------------------
# LATEX
# ---------------------------------------------------------------------------

def _render_latex(latex, output_dir, index, fontsize=14):
    """
    Renderizza una formula LaTeX tramite matplotlib.
    """

    filename = os.path.join(
        output_dir,
        f"formula_{index}.png",
    )

    fig = plt.figure(figsize=(0.01, 0.01))

    fig.text(
        0,
        0,
        f"${latex}$",
        fontsize=fontsize,
    )

    fig.savefig(
        filename,
        format="png",
        dpi=200,
        transparent=True,
        bbox_inches="tight",
        pad_inches=0.05,
    )

    plt.close(fig)

    return filename


# ---------------------------------------------------------------------------
# CONTENUTO
# ---------------------------------------------------------------------------

def _add_text_with_inline_math(
    story,
    text,
    asset_dir,
    formula_counter,
    styles,
):
    """
    Gestisce testo contenente formule inline $...$.
    """

    pattern = re.compile(
        r"\$(?!\$)(.+?)(?<!\$)\$"
    )

    matches = list(pattern.finditer(text))

    if not matches:
        if text.strip():
            story.append(
                _text_to_paragraph(
                    text,
                    styles,
                )
            )

        return formula_counter

    cursor = 0

    for match in matches:

        before = text[cursor:match.start()]

        if before.strip():
            story.append(
                _text_to_paragraph(
                    before,
                    styles,
                )
            )

        latex = match.group(1).strip()

        image_path = _render_latex(
            latex,
            asset_dir,
            formula_counter,
            fontsize=12,
        )

        img = Image(image_path)

        img.drawHeight = 0.45 * cm
        img.drawWidth = (
            0.45 * cm * max(1, len(latex) ** 0.35)
        )

        story.append(img)

        formula_counter += 1
        cursor = match.end()

    remaining = text[cursor:]

    if remaining.strip():
        story.append(
            _text_to_paragraph(
                remaining,
                styles,
            )
        )

    return formula_counter


def _add_content(
    story,
    text,
    asset_dir,
    formula_counter,
    styles,
):
    """
    Converte il testo grezzo in elementi ReportLab.

    Gestisce:
    - blocchi ```...```
    - $$...$$
    - $...$
    - testo normale
    """

    if not text:
        return formula_counter

    text = str(text).replace(
        "\r\n",
        "\n",
    )

    parts = re.split(
        r"```(.*?)```",
        text,
        flags=re.DOTALL,
    )

    for i, part in enumerate(parts):

        # ===============================================================
        # CODICE
        # ===============================================================

        if i % 2 == 1:

            code = part.strip()

            if code.startswith("python"):
                code = code[len("python"):].lstrip("\n")

            code = _escape_text(code)

            story.append(
                Paragraph(
                    code.replace("\n", "<br/>"),
                    styles["code"],
                )
            )

            continue

        # ===============================================================
        # TESTO
        # ===============================================================

        normal_text = part.strip()

        if not normal_text:
            continue

        display_parts = re.split(
            r"\$\$(.+?)\$\$",
            normal_text,
            flags=re.DOTALL,
        )

        for j, display_part in enumerate(display_parts):

            # -----------------------------------------------------------
            # FORMULA DISPLAY
            # -----------------------------------------------------------

            if j % 2 == 1:

                latex = display_part.strip()

                image_path = _render_latex(
                    latex,
                    asset_dir,
                    formula_counter,
                    fontsize=16,
                )

                img = Image(image_path)

                max_width = 15 * cm
                max_height = 4 * cm

                width = img.imageWidth
                height = img.imageHeight

                scale = min(
                    max_width / width,
                    max_height / height,
                    1,
                )

                img.drawWidth = width * scale
                img.drawHeight = height * scale

                story.append(
                    Spacer(1, 0.1 * cm)
                )

                story.append(img)

                story.append(
                    Spacer(1, 0.1 * cm)
                )

                formula_counter += 1

                continue

            # -----------------------------------------------------------
            # PARAGRAFI
            # -----------------------------------------------------------

            paragraph_text = display_part.strip()

            if not paragraph_text:
                continue

            paragraphs = re.split(
                r"\n\s*\n",
                paragraph_text,
            )

            for paragraph in paragraphs:

                paragraph = paragraph.strip()

                if not paragraph:
                    continue

                formula_counter = _add_text_with_inline_math(
                    story,
                    paragraph,
                    asset_dir,
                    formula_counter,
                    styles,
                )

    return formula_counter


# ---------------------------------------------------------------------------
# SCIENCE
# ---------------------------------------------------------------------------

def _add_science_day(
    story,
    topic,
    asset_dir,
    formula_counter,
    styles,
):
    """
    Aggiunge un singolo giorno/topic di Science.
    """

    name = _escape_text(
        topic.get("name", "Science")
    )

    day = topic.get("day")
    track_days = topic.get("track_days")

    if day is not None and track_days is not None:
        title = f"{name} — giorno {day}/{track_days}"
    else:
        title = name

    story.append(
        Paragraph(
            title,
            styles["day"],
        )
    )

    formula_counter = _add_content(
        story,
        topic.get("text", ""),
        asset_dir,
        formula_counter,
        styles,
    )

    return formula_counter


# ---------------------------------------------------------------------------
# SEZIONI
# ---------------------------------------------------------------------------

def _add_section_header(
    story,
    number,
    title,
    styles,
):
    story.append(
        Paragraph(
            f"{number}. {_escape_text(title)}",
            styles["section"],
        )
    )


def _add_generic_day(
    story,
    label,
    content,
    asset_dir,
    formula_counter,
    styles,
):
    """
    Aggiunge il contenuto di una sezione per un determinato giorno.
    """

    story.append(
        Paragraph(
            _escape_text(label),
            styles["day"],
        )
    )

    formula_counter = _add_content(
        story,
        content,
        asset_dir,
        formula_counter,
        styles,
    )

    return formula_counter


# ---------------------------------------------------------------------------
# NEWS
# ---------------------------------------------------------------------------

def _add_news(
    story,
    entries,
    styles,
):
    """
    Aggiunge tutte le news della settimana.
    """

    _add_section_header(
        story,
        7,
        "News",
        styles,
    )

    for entry in entries:

        entry_date = entry.get(
            "date",
            "",
        )

        news = entry.get(
            "news",
            {},
        )

        if not news:
            continue

        story.append(
            Paragraph(
                _escape_text(entry_date),
                styles["day"],
            )
        )

        summary = news.get(
            "summary",
            "",
        )

        if summary:
            story.append(
                _text_to_paragraph(
                    summary,
                    styles,
                )
            )

        for article in news.get(
            "articles",
            [],
        ):
            title = _escape_text(
                article.get(
                    "title",
                    "Articolo",
                )
            )

            source = _escape_text(
                article.get(
                    "source",
                    "",
                )
            )

            link = article.get(
                "link",
                "",
            )

            text = f"<b>{title}</b>"

            if source:
                text += f" — {source}"

            if link:
                text += f"<br/>{_escape_text(link)}"

            story.append(
                Paragraph(
                    text,
                    styles["body"],
                )
            )


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def build_weekly_report():
    """
    Genera il PDF settimanale.

    Il report è organizzato per sezione:

        Science
            giorno 1
            giorno 2

        Reading
            giorno 1
            giorno 2

        ...

    Il weekly log viene svuotato solamente dopo la generazione
    corretta del PDF.

    Returns
    -------
    str | None
        Percorso del PDF, oppure None se non ci sono dati.
    """

    if not os.path.exists(LOG_PATH):
        return None

    with open(
        LOG_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        log = json.load(f)

    entries = log.get(
        "entries",
        [],
    )

    if not entries:
        return None

    os.makedirs(
        REPORTS_DIR,
        exist_ok=True,
    )

    filename = os.path.join(
        REPORTS_DIR,
        f"{date.today().isoformat()}_resoconto_settimanale.pdf",
    )

    styles = _get_styles()

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Resoconto settimanale",
    )

    story = []

    # Immagini temporanee per le formule.
    with tempfile.TemporaryDirectory() as asset_dir:

        # ===============================================================
        # TITOLO
        # ===============================================================

        first_date = entries[0].get(
            "date",
            "",
        )

        last_date = entries[-1].get(
            "date",
            "",
        )

        story.append(
            Paragraph(
                "Resoconto settimanale",
                styles["title"],
            )
        )

        if first_date and last_date:
            story.append(
                Paragraph(
                    f"{_escape_text(first_date)} — "
                    f"{_escape_text(last_date)}",
                    styles["body"],
                )
            )

        story.append(
            Spacer(1, 0.4 * cm)
        )

        formula_counter = 0

        # ===============================================================
        # 1. SCIENCE
        # ===============================================================

        _add_section_header(
            story,
            1,
            "Science",
            styles,
        )

        for entry in entries:

            entry_date = entry.get(
                "date",
                "",
            )

            for topic in entry.get(
                "science",
                [],
            ):

                label = entry_date

                if topic.get("day") is not None:
                    label += (
                        f" — giorno "
                        f"{topic['day']}/{topic['track_days']}"
                    )

                label += (
                    f" — {topic.get('name', '')}"
                )

                formula_counter = _add_generic_day(
                    story,
                    label,
                    topic.get("text", ""),
                    asset_dir,
                    formula_counter,
                    styles,
                )

        # ===============================================================
        # 2. READING
        # ===============================================================

        _add_section_header(
            story,
            2,
            "Reading",
            styles,
        )

        for entry in entries:

            reading = entry.get(
                "reading",
            )

            if not reading:
                continue

            label = entry.get(
                "date",
                "",
            )

            if reading.get("book"):
                label += f" — {reading['book']}"

            if reading.get("day_in_block") is not None:
                label += (
                    f" — blocco "
                    f"{reading['day_in_block']}"
                )

            formula_counter = _add_generic_day(
                story,
                label,
                reading.get("text", ""),
                asset_dir,
                formula_counter,
                styles,
            )

        # ===============================================================
        # 3. PHILOSOPHY
        # ===============================================================

        _add_section_header(
            story,
            3,
            "Philosophy",
            styles,
        )

        for entry in entries:

            philosophy = entry.get(
                "philosophy",
            )

            if not philosophy:
                continue

            label = entry.get(
                "date",
                "",
            )

            if philosophy.get("philosopher"):
                label += (
                    f" — {philosophy['philosopher']}"
                )

            if philosophy.get("day_in_block") is not None:
                label += (
                    f" — giorno "
                    f"{philosophy['day_in_block']}"
                )

            formula_counter = _add_generic_day(
                story,
                label,
                philosophy.get("text", ""),
                asset_dir,
                formula_counter,
                styles,
            )

        # ===============================================================
        # 4. GERMAN
        # ===============================================================

        _add_section_header(
            story,
            4,
            "German",
            styles,
        )

        for entry in entries:

            german = entry.get(
                "german",
            )

            if not german:
                continue

            label = entry.get(
                "date",
                "",
            )

            formula_counter = _add_generic_day(
                story,
                label,
                german.get("text", ""),
                asset_dir,
                formula_counter,
                styles,
            )

        # ===============================================================
        # 5. CODING
        # ===============================================================

        _add_section_header(
            story,
            5,
            "Coding",
            styles,
        )

        for entry in entries:

            coding = entry.get(
                "coding",
            )

            if not coding:
                continue

            label = entry.get(
                "date",
                "",
            )

            formula_counter = _add_generic_day(
                story,
                label,
                coding.get("text", ""),
                asset_dir,
                formula_counter,
                styles,
            )

        # ===============================================================
        # 6. POKER
        # ===============================================================

        _add_section_header(
            story,
            6,
            "Poker theory",
            styles,
        )

        for entry in entries:

            poker = entry.get(
                "poker",
            )

            if not poker:
                continue

            label = entry.get(
                "date",
                "",
            )

            formula_counter = _add_generic_day(
                story,
                label,
                poker.get("text", ""),
                asset_dir,
                formula_counter,
                styles,
            )

        # ===============================================================
        # 7. NEWS
        # ===============================================================

        _add_news(
            story,
            entries,
            styles,
        )

        # ===============================================================
        # FEEDBACK
        # ===============================================================

        feedback_entries = []

        for entry in entries:
            for change in entry.get(
                "feedback_changes",
                [],
            ):
                feedback_entries.append(
                    (
                        entry.get("date", ""),
                        change,
                    )
                )

        if feedback_entries:

            _add_section_header(
                story,
                8,
                "Feedback applicato",
                styles,
            )

            for entry_date, change in feedback_entries:

                story.append(
                    Paragraph(
                        f"<b>{_escape_text(entry_date)}</b> — "
                        f"{_escape_text(change)}",
                        styles["body"],
                    )
                )

        # ===============================================================
        # GENERAZIONE PDF
        # ===============================================================

        doc.build(story)

    # ===============================================================
    # SVUOTA IL LOG SOLO DOPO LA GENERAZIONE DEL PDF
    # ===============================================================

    with open(
        LOG_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {"entries": []},
            f,
            ensure_ascii=False,
            indent=2,
        )

    return filename

