import os
from pythonEmailNotify import EmailSender

sender = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    login=os.getenv("EMAIL_ADDRESS"),
    password=os.getenv("EMAIL_PASSWORD"),
    default_recipient=os.getenv("MAIN_EMAIL_ADDRESS"),
)

sender.sendEmail(
    subject="pythonEmailNotify test",
    body="Test message sent using environment variables.",
)
