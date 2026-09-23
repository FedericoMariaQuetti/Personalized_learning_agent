"""
send_email.py
-------------
Invia l'email della newsletter tramite Gmail (SMTP), usando una
"App Password" di Google (NON la password normale del tuo account).

Come creare l'App Password:
1. Vai su https://myaccount.google.com/security
2. Attiva la verifica in due passaggi (se non l'hai già)
3. Cerca "Password per le app" e generane una nuova
4. Usa quella password nel secret GMAIL_APP_PASSWORD
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject, html_content):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    recipients = [r.strip() for r in os.environ["RECIPIENT_EMAIL"].split(",")]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
