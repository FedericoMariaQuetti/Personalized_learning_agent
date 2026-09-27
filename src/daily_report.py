"""
daily_report.py
---------------
Genera il PDF giornaliero del percorso di apprendimento.

Riceve contenuti in testo grezzo/Markdown e li trasforma in un PDF,
gestendo:
- testo normale
- formule LaTeX inline: $...$
- formule LaTeX display: $$...$$
- blocchi di codice: ```...```
"""

import html
import os
import re
import tempfile

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


REPORTS_DIR = "reports/daily"


# ---------------------------------------------------------------------------
# STILI
# ---------------------------------------------------------------------------

def _get_styles():
    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "DailyTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            spaceAfter=18,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            spaceBefore=14,
            spaceAfter=10,
        ),
        "subsection": ParagraphStyle(
            "Subsection",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=15,
            spaceAfter=8,
        ),
        "code": ParagraphStyle(
            "Code",
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
            "Formula",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            spaceBefore=8,
            spaceAfter=8,
        ),
    }


# ---------------------------------------------------------------------------
# LATEX
# ---------------------------------------------------------------------------

def _render_latex(latex, output_dir, index, fontsize=14):
    """
    Renderizza una formula LaTeX tramite matplotlib e restituisce
    il percorso del PNG generato.
    """

    filename = os.path.join(output_dir, f"formula_{index}.png")

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
# TESTO
# ---------------------------------------------------------------------------

def _escape_text(text):
    """
    Escape dei caratteri speciali HTML utilizzati da ReportLab Paragraph.
    """

    return html.escape(text, quote=False)


def _convert_basic_markdown(text):
    """
    Converte solo una piccola parte del Markdown in markup comprensibile
    a ReportLab.

    Supporta:
    **grassetto**
    *corsivo*
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


def _text_to_paragraph(text):
    """
    Prepara una porzione di testo normale per ReportLab.
    """

    text = _escape_text(text)
    text = _convert_basic_markdown(text)

    # Mantiene eventuali singoli a-capo.
    text = text.replace("\n", "<br/>")

    return Paragraph(
        text,
        _get_styles()["body"],
    )


# ---------------------------------------------------------------------------
# PARSING DEI CONTENUTI
# ---------------------------------------------------------------------------

def _add_text_with_inline_math(
    story,
    text,
    asset_dir,
    formula_counter,
):
    """
    Gestisce testo normale contenente formule LaTeX inline del tipo:

        La varianza è $\\sigma^2$.

    Le formule vengono convertite in immagini.
    """

    pattern = re.compile(r"\$(?!\$)(.+?)(?<!\$)\$")

    matches = list(pattern.finditer(text))

    if not matches:
        if text.strip():
            story.append(_text_to_paragraph(text))
        return formula_counter

    cursor = 0

    for match in matches:
        before = text[cursor:match.start()]

        if before.strip():
            story.append(_text_to_paragraph(before))

        latex = match.group(1).strip()

        image_path = _render_latex(
            latex,
            asset_dir,
            formula_counter,
            fontsize=12,
        )

        img = Image(image_path)

        # Dimensione ragionevole per formule inline.
        img.drawHeight = 0.45 * cm
        img.drawWidth = 0.45 * cm * max(1, len(latex) ** 0.35)

        story.append(img)

        formula_counter += 1
        cursor = match.end()

    remaining = text[cursor:]

    if remaining.strip():
        story.append(_text_to_paragraph(remaining))

    return formula_counter


def _add_content(
    story,
    text,
    asset_dir,
    formula_counter,
):
    """
    Converte il contenuto grezzo di una sezione in elementi ReportLab.

    Riconosce:
    - blocchi ```...```
    - formule $$...$$
    - formule inline $...$
    - testo normale
    """

    if not text:
        return formula_counter

    # Normalizza i line ending.
    text = text.replace("\r\n", "\n")

    # Divide il testo in blocchi di codice e testo normale.
    parts = re.split(r"```(.*?)```", text, flags=re.DOTALL)

    for i, part in enumerate(parts):

        # ---------------------------------------------------------------
        # BLOCCO DI CODICE
        # ---------------------------------------------------------------

        if i % 2 == 1:
            code = part.strip()

            # Rimuove eventualmente il linguaggio indicato:
            # ```python
            if code.startswith("python"):
                code = code[len("python"):].lstrip("\n")

            code = _escape_text(code)

            story.append(
                Paragraph(
                    code.replace("\n", "<br/>"),
                    _get_styles()["code"],
                )
            )

            continue

        # ---------------------------------------------------------------
        # TESTO NORMALE
        # ---------------------------------------------------------------

        normal_text = part.strip()

        if not normal_text:
            continue

        # Separazione dei blocchi $$...$$.
        display_parts = re.split(
            r"\$\$(.+?)\$\$",
            normal_text,
            flags=re.DOTALL,
        )

        for j, display_part in enumerate(display_parts):

            # Formula display
            if j % 2 == 1:
                latex = display_part.strip()

                image_path = _render_latex(
                    latex,
                    asset_dir,
                    formula_counter,
                    fontsize=16,
                )

                img = Image(image_path)

                # Limiti ragionevoli per la pagina A4.
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

            # Testo normale
            else:
                paragraph_text = display_part.strip()

                if paragraph_text:
                    # Separiamo paragrafi consecutivi.
                    paragraphs = re.split(
                        r"\n\s*\n",
                        paragraph_text,
                    )

                    for paragraph in paragraphs:
                        paragraph = paragraph.strip()

                        if paragraph:
                            formula_counter = _add_text_with_inline_math(
                                story,
                                paragraph,
                                asset_dir,
                                formula_counter,
                            )

    return formula_counter


# ---------------------------------------------------------------------------
# SEZIONI
# ---------------------------------------------------------------------------

def _add_section(
    story,
    number,
    title,
    content,
    asset_dir,
    formula_counter,
):
    """
    Aggiunge una sezione del curriculum.
    """

    story.append(
        Paragraph(
            f"{number}. {html.escape(title)}",
            _get_styles()["section"],
        )
    )

    formula_counter = _add_content(
        story,
        content,
        asset_dir,
        formula_counter,
    )

    story.append(Spacer(1, 0.25 * cm))

    return formula_counter


# ---------------------------------------------------------------------------
# NEWS
# ---------------------------------------------------------------------------

def _add_news(
    story,
    news_summary,
    articles,
):
    story.append(
        Paragraph(
            "7. News",
            _get_styles()["section"],
        )
    )

    if news_summary:
        story.append(
            _text_to_paragraph(news_summary)
        )

    if articles:
        for article in articles:
            title = _escape_text(
                article.get("title", "Articolo")
            )
            source = _escape_text(
                article.get("source", "")
            )

            text = f"<b>{title}</b>"

            if source:
                text += f" — {source}"

            story.append(
                Paragraph(
                    text,
                    _get_styles()["body"],
                )
            )


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def build_daily_report(
    sections,
    news_summary,
    articles,
    report_date,
):
    """
    Genera il PDF giornaliero.

    Parameters
    ----------
    sections : dict
        Dizionario del tipo:

        {
            "science": "...",
            "reading": "...",
            "philosophy": "...",
            "german": "...",
            "coding": "...",
            "poker": "..."
        }

    news_summary : str
        Sintesi delle notizie.

    articles : list
        Lista degli articoli RSS.

    report_date : date
        Data del percorso.

    Returns
    -------
    str
        Percorso del PDF generato.
    """

    os.makedirs(REPORTS_DIR, exist_ok=True)

    filename = os.path.join(
        REPORTS_DIR,
        f"{report_date.isoformat()}_percorso.pdf",
    )

    styles = _get_styles()

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Il tuo percorso di oggi — {report_date.isoformat()}",
    )

    story = []

    # Directory temporanea per le immagini delle formule.
    with tempfile.TemporaryDirectory() as asset_dir:

        # ---------------------------------------------------------------
        # TITOLO
        # ---------------------------------------------------------------

        story.append(
            Paragraph(
                "Il tuo percorso di oggi",
                styles["title"],
            )
        )

        story.append(
            Paragraph(
                report_date.strftime("%d/%m/%Y"),
                styles["body"],
            )
        )

        story.append(Spacer(1, 0.3 * cm))

        formula_counter = 0

        # ---------------------------------------------------------------
        # 6 SEZIONI
        # ---------------------------------------------------------------

        section_definitions = [
            ("science", "Science"),
            ("reading", "Reading"),
            ("philosophy", "Philosophy"),
            ("german", "German"),
            ("coding", "Coding"),
            ("poker", "Poker theory"),
        ]

        for number, (key, title) in enumerate(
            section_definitions,
            start=1,
        ):
            content = sections.get(key, "")

            formula_counter = _add_section(
                story,
                number,
                title,
                content,
                asset_dir,
                formula_counter,
            )

        # ---------------------------------------------------------------
        # NEWS
        # ---------------------------------------------------------------

        _add_news(
            story,
            news_summary,
            articles,
        )

        # ---------------------------------------------------------------
        # GENERAZIONE PDF
        # ---------------------------------------------------------------

        doc.build(story)

    return filename
