from pythonEmailNotify import *
import os
#This is a test script to test email notifications
emailSender = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    login=os.getenv("EMAIL_ADDRESS"), # enter your email address if not using environment variables
    password=os.getenv("EMAIL_PASSWORD"),# enter your password address if not using environment variables
    default_recipient=os.getenv("MAIN_EMAIL_ADDRESS")  # Send exception reports to yourself
)

try:
    # Simulate some code that might fail
    result = 1 / 0  # This will raise a ZeroDivisionError
except Exception as e:
    # Send an email with the exception details
    emailSender.sendException(e)