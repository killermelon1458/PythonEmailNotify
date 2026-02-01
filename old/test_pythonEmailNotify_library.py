"""
test_pythonEmailNotify_library.py

Thorough abuse-testing of pythonEmailNotify in *library mode*.
Assumes the following env vars exist:

EMAIL_ADDRESS
EMAIL_PASSWORD
MAIN_EMAIL_ADDRESS
"""

import os
import traceback
from pythonEmailNotify_v3 import EmailSender, send_email
from pythonEmailNotify_v3 import (
    ConfigurationError,
    AuthenticationError,
    NetworkError,
    SmtpError,
)

# -------------------------
# Helpers
# -------------------------
def banner(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def expect_exception(label, exc_type, func):
    print(f"\n[TEST] {label}")
    try:
        func()
    except exc_type as e:
        print(f"[OK] Caught expected {exc_type.__name__}: {e}")
    except Exception as e:
        print(f"[FAIL] Unexpected exception type: {type(e).__name__}")
        traceback.print_exc()
    else:
        print("[FAIL] Expected exception but nothing was raised")


def expect_success(label, func):
    print(f"\n[TEST] {label}")
    try:
        result = func()
        print(f"[OK] Success, return value = {result}")
    except Exception as e:
        print(f"[FAIL] Unexpected exception: {e}")
        traceback.print_exc()


# -------------------------
# Load env vars
# -------------------------
EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT = os.getenv("MAIN_EMAIL_ADDRESS")

assert EMAIL, "EMAIL_ADDRESS env var missing"
assert PASSWORD, "EMAIL_PASSWORD env var missing"
assert RECIPIENT, "MAIN_EMAIL_ADDRESS env var missing"


# -------------------------
# 1. Happy path
# -------------------------
banner("1. HAPPY PATH")

expect_success(
    "Send plain text email",
    lambda: send_email(
        subject="pythonEmailNotify test – happy path",
        message="This is a plain text test.",
        to=RECIPIENT,
        login=EMAIL,
        password=PASSWORD,
    ),
)

expect_success(
    "Send HTML email",
    lambda: send_email(
        subject="pythonEmailNotify test – HTML",
        message="<h1>HTML test</h1><p>This is HTML.</p>",
        to=RECIPIENT,
        login=EMAIL,
        password=PASSWORD,
        html=True,
    ),
)


# -------------------------
# 2. Configuration errors
# -------------------------
banner("2. CONFIGURATION ERRORS")

expect_exception(
    "Missing SMTP server",
    ConfigurationError,
    lambda: EmailSender(
        smtp_server=None,
        port=587,
        login=EMAIL,
        password=PASSWORD,
        default_recipient=RECIPIENT,
    ),
)

expect_exception(
    "Invalid port (string)",
    ConfigurationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port="not_a_port",
        login=EMAIL,
        password=PASSWORD,
        default_recipient=RECIPIENT,
    ),
)

expect_exception(
    "Invalid port (out of range)",
    ConfigurationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=99999,
        login=EMAIL,
        password=PASSWORD,
        default_recipient=RECIPIENT,
    ),
)

expect_exception(
    "Missing login",
    ConfigurationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=587,
        login=None,
        password=PASSWORD,
        default_recipient=RECIPIENT,
    ),
)

expect_exception(
    "Missing password",
    ConfigurationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=587,
        login=EMAIL,
        password=None,
        default_recipient=RECIPIENT,
    ),
)

expect_exception(
    "TLS and SSL both enabled",
    ConfigurationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=587,
        login=EMAIL,
        password=PASSWORD,
        default_recipient=RECIPIENT,
        use_tls=True,
        use_ssl=True,
    ),
)


# -------------------------
# 3. Authentication failures
# -------------------------
banner("3. AUTHENTICATION FAILURES")

expect_exception(
    "Wrong password",
    AuthenticationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=587,
        login=EMAIL,
        password="definitely_wrong_password",
        default_recipient=RECIPIENT,
        raise_on_failure=True,
    ).sendEmail(
        subject="should fail",
        body="bad password test",
    ),
)


# -------------------------
# 4. Network failures
# -------------------------
banner("4. NETWORK FAILURES")

expect_exception(
    "Bad SMTP hostname (DNS failure)",
    NetworkError,
    lambda: EmailSender(
        smtp_server="smtp.this-domain-should-not-exist.example",
        port=587,
        login=EMAIL,
        password=PASSWORD,
        default_recipient=RECIPIENT,
        raise_on_failure=True,
    ).sendEmail(
        subject="dns failure test",
        body="this should never send",
    ),
)

expect_exception(
    "Connection refused (wrong port)",
    NetworkError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=1,
        login=EMAIL,
        password=PASSWORD,
        default_recipient=RECIPIENT,
        raise_on_failure=True,
    ).sendEmail(
        subject="connection refused test",
        body="this should never send",
    ),
)


# -------------------------
# 5. Caller misuse
# -------------------------
banner("5. CALLER MISUSE")

expect_exception(
    "No recipient anywhere",
    ConfigurationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=587,
        login=EMAIL,
        password=PASSWORD,
        default_recipient=None,
        raise_on_failure=True,
    ).sendEmail(
        subject="no recipient",
        body="this should fail",
    ),
)

expect_exception(
    "Empty recipient list",
    ConfigurationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=587,
        login=EMAIL,
        password=PASSWORD,
        default_recipient="",
        raise_on_failure=True,
    ).sendEmail(
        subject="empty recipient",
        body="this should fail",
    ),
)


# -------------------------
# 6. Failure-handling behavior
# -------------------------
banner("6. FAILURE HANDLING BEHAVIOR")

print("\n[TEST] raise_on_failure=False should NOT raise")
sender = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    login=EMAIL,
    password="wrong_password",
    default_recipient=RECIPIENT,
    raise_on_failure=False,
)
ok = sender.sendEmail(
    subject="should fail silently but loudly logged",
    body="failure handling test",
)
print(f"[OK] Returned {ok}, last_error = {type(sender.last_error).__name__}")

print("\n[TEST] raise_on_failure=True SHOULD raise")
expect_exception(
    "raise_on_failure=True raises",
    AuthenticationError,
    lambda: EmailSender(
        smtp_server="smtp.gmail.com",
        port=587,
        login=EMAIL,
        password="wrong_password",
        default_recipient=RECIPIENT,
        raise_on_failure=True,
    ).sendEmail(
        subject="should raise",
        body="failure handling test",
    ),
)

print("\nALL LIBRARY TESTS COMPLETED")
