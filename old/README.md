# pythonEmailNotify

A lightweight Python module for sending email notifications, including exception reports, using SMTP. Ideal for monitoring Python scripts and automatically reporting failures via email.

## Features

- Send plain text or HTML-formatted emails
- Centralized exception reporting via email
- Optional support for environment variable-based authentication
- Simple and modular `EmailSender` class for reusability

## Files

| File               | Description                                              |
|--------------------|----------------------------------------------------------|
| `pythonEmailNotify.py` | Core module that defines the `EmailSender` class       |
| `emailTest.py`         | Test script that demonstrates exception reporting      |
| `envVarTest.py`        | Sample script for testing environment variable loading |
| `genEmailTest.py`      | Additional test script (for custom message testing)    |

## Setup

1. **Install Python (3.6+)**
2. **Set up environment variables** (optional but recommended):

   ```bash
   export EMAIL_ADDRESS="your_email@example.com"
   export EMAIL_PASSWORD="your_email_password"
   export MAIN_EMAIL_ADDRESS="recipient_email@example.com"
   ```

   Or set them using your system’s environment editor.

3. **Install dependencies** (if not already installed — only standard library is used).

4. **Run the test script**:

   ```bash
   python emailTest.py
   ```

   This will trigger a `ZeroDivisionError` and send the exception details via email.

## Usage Example

```python
from pythonEmailNotify import EmailSender
import os

emailSender = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    login=os.getenv("EMAIL_ADDRESS"),
    password=os.getenv("EMAIL_PASSWORD"),
    default_recipient=os.getenv("MAIN_EMAIL_ADDRESS")
)

try:
    # your risky code here
    risky = 10 / 0
except Exception as e:
    emailSender.sendException(e)
```

## Security Tip

Use **App Passwords** for Gmail if 2FA is enabled, and **never** hard-code credentials directly in the script.

## License

MIT License (or specify your own here)
