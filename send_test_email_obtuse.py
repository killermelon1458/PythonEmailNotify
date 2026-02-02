"""
Minimal smoke test for pythonEmailNotify.

This script verifies:
- The python_email_notify package is importable
- Environment variables are readable
- SMTP credentials are valid
- Email sending works end-to-end

It is intentionally simple and has no error handling.
All failures are expected to print loud diagnostics to stderr.
"""

import os
from python_email_notify import EmailSender


# Read configuration from environment variables.
# These should be set by the shell, systemd service, or test harness.
sender = EmailSender(
    smtp_server=os.getenv("OBTUSE_SMTP_SERVER"),
    port=int(os.getenv("OBTUSE_SMTP_PORT", "0")),
    login=os.getenv("OBTUSE_EMAIL_USERNAME"),
    password=os.getenv("OBTUSE_EMAIL_PASSWORD"),
    default_recipient=os.getenv("OBTUSE_EMAIL_DEFAULT_RECIPIENT"),
)

# Attempt a single email send.
# Return value is True on success, False on failure.
sender.sendEmail(
    subject="pythonEmailNotify smoke test",
    body="Test message sent using environment-based configuration."
)
