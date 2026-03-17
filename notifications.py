import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "rvlife9269@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "uyqrrtunozxuwcmk")
NOTIFY_FROM = "APPTS System"
ENABLED = bool(SMTP_USER and SMTP_PASS)


def _send(to_email, subject, html):
    print(f"[NOTIFY] Sending to {to_email}: {subject}")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{NOTIFY_FROM} <{SMTP_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"[NOTIFY] SUCCESS email sent to {to_email}")
    except Exception as e:
        print(f"[NOTIFY] FAILED: {type(e).__name__}: {e}")
