"""
send_email.py
-------------
Invia l'email tramite Gmail (SMTP), usando una "App Password" di Google.
Supporta allegati PDF.
"""

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject, body="", attachment_path=None):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]

    recipients = [
        r.strip()
        for r in os.environ["RECIPIENT_EMAIL"].split(",")
    ]

    # ---------------------------------------------------------------
    # MESSAGGIO
    # ---------------------------------------------------------------

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)

    # Corpo dell'email.
    # Può essere vuoto: il contenuto principale può essere
    # esclusivamente il PDF allegato.
    msg.attach(
        MIMEText(body, "plain", "utf-8")
    )

    # ---------------------------------------------------------------
    # ALLEGATO
    # ---------------------------------------------------------------

    if attachment_path:
        if not os.path.exists(attachment_path):
            raise FileNotFoundError(
                f"Allegato non trovato: {attachment_path}"
            )

        with open(attachment_path, "rb") as f:
            attachment = MIMEApplication(
                f.read(),
                _subtype="pdf",
            )

        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=os.path.basename(attachment_path),
        )

        msg.attach(attachment)

    # ---------------------------------------------------------------
    # INVIO
    # ---------------------------------------------------------------

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
    ) as server:

        server.login(
            gmail_user,
            gmail_password,
        )

        server.sendmail(
            gmail_user,
            recipients,
            msg.as_string(),
        )
