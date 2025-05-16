from pythonEmailNotify import *
import os
# Initialize the email sender
emailSender = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    login=os.getenv("EMAIL_ADDRESS"),
    password=os.getenv("EMAIL_PASSWORD"),
    default_recipient=os.getenv("MAIN_EMAIL_ADDRESS")
)

# Send a test email
emailSender.sendEmail(
    subject="Test Email",
    body="This is a test email sent from my reusable email module."
)
