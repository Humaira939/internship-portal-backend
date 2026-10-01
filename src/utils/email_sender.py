import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.utils.settings import settings


def send_reset_email(to_email: str, reset_link: str):
    message = MIMEMultipart()
    message["From"] = settings.EMAIL_ADDRESS
    message["To"] = to_email
    message["Subject"] = "SmartIntern - Reset your password"

    body = (
        "We received a request to reset your SmartIntern password.\n\n"
        f"Click the link below to set a new password (valid for 15 minutes):\n{reset_link}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings.EMAIL_ADDRESS, settings.EMAIL_APP_PASSWORD)
        server.send_message(message)