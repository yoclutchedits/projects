import smtplib
from email.mime.text import MIMEText
import os

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_verification_email(to_email: str, code: str):
    subject = "Your verification code"
    body = f"Your verification code is: {code}\n\nThis code expires soon, so use it quickly."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"[EMAIL SENT] to {to_email}")
    except Exception as e:
        print(f"[EMAIL FAILED] {e}")