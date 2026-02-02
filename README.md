# pythonEmailNotify

A hardened, dependency-free Python library for sending **reliable, non-blocking email notifications**
from scripts, services, and infrastructure tooling.

This library is designed for **production environments** where failures must be **loud**,
logging must **never hang**, and email delivery attempts must be **predictable and observable**.

---

## Key Properties

* **Fail-loud by design**

  * All failures are printed to `stderr` with timestamps
  * No silent errors
  * Explicit diagnostics for misconfiguration and runtime failures

* **Non-blocking logging**

  * Logging is optional and opt-in
  * Logging cannot block or hang the calling process
  * Filesystem failures never stop execution

* **No retries, no hidden state**

  * One send attempt per call
  * No background retry loops
  * No implicit queues or persistence

* **Backwards-compatible API**

  * Stable constructor and method names
  * Safe defaults
  * Optional strict validation mode

* **Minimal dependencies**

  * Python standard library only
  * No external packages
  * Works on Windows, Linux, headless systems, cron, and systemd

---

## Intended Use Cases

* systemd `OnFailure=` hooks
* Cron job failure notifications
* Watchdog scripts
* Backup and retention jobs
* Headless servers
* Homelab and infrastructure automation
* One-shot alerts from Python scripts

This is **not** a bulk mailer or guaranteed delivery system.
It is a **notification helper**, not a messaging platform.

---

## Non-Goals (Explicit)

This library intentionally does **not** provide:

* Retry policies
* Delivery guarantees
* Persistent queues
* Rate limiting
* Async APIs
* Templating engines

Those concerns belong in higher-level systems.

---

## Installation

This project is distributed as a **proper Python package** and is typically installed
in **editable mode** for infrastructure use.

```bash
git clone https://github.com/killermelon1458/PythonEmailNotify.git
cd PythonEmailNotify
pip install --user -e . --break-system-packages
```

Editable installs ensure that updates take effect immediately after `git pull`.

---

## Basic Usage

```python
from python_email_notify import EmailSender

sender = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    login="sender@example.com",
    password="app_password_here",
    default_recipient="alerts@example.com"
)

sender.sendEmail(
    subject="Job completed",
    body="The scheduled job finished successfully."
)
```

### Return value

* `True` → email send attempt succeeded
* `False` → failure occurred (details printed to stderr)

---

## Environment Variable Pattern (Recommended)

Credentials and configuration are commonly injected via environment variables:

```bash
OBTUSE_SMTP_SERVER=smtp.gmail.com
OBTUSE_SMTP_PORT=587
OBTUSE_EMAIL_USERNAME=sender@example.com
OBTUSE_EMAIL_PASSWORD=app_password
OBTUSE_EMAIL_DEFAULT_RECIPIENT=alerts@example.com
```

```python
import os
from python_email_notify import EmailSender

sender = EmailSender(
    smtp_server=os.getenv("OBTUSE_SMTP_SERVER"),
    port=int(os.getenv("OBTUSE_SMTP_PORT")),
    login=os.getenv("OBTUSE_EMAIL_USERNAME"),
    password=os.getenv("OBTUSE_EMAIL_PASSWORD"),
    default_recipient=os.getenv("OBTUSE_EMAIL_DEFAULT_RECIPIENT"),
)
```

If variables are missing or invalid, the library prints **explicit diagnostics**
and fails sends loudly.

---

## Exception Reporting

Send a full exception report (including traceback):

```python
try:
    risky_operation()
except Exception as e:
    sender.sendException(e)
```

* Captures the actual exception traceback
* Works even outside the original `except` context
* Does not crash if email sending fails

---

## Runtime Configuration (Environment-Driven)

### Enable / Disable Logging

```bash
PYTHON_EMAIL_NOTIFY_ENABLE_LOGGING=1   # default
PYTHON_EMAIL_NOTIFY_ENABLE_LOGGING=0   # disable
```

Logging is:

* Asynchronous
* Non-blocking
* Never fatal

---

### Log Directory (Opt-In)

```bash
PYTHON_EMAIL_NOTIFY_LOG_DIR=/var/log/pythonEmailNotify
```

If unset or empty:

* **No log files are written**
* All diagnostics still go to `stderr`

The library never writes logs by default.

---

### Strict Configuration Validation

```bash
PYTHON_EMAIL_NOTIFY_STRICT_CONFIG=1
```

* `0` (default): invalid config prints diagnostics and fails sends loudly
* `1`: invalid config raises `ValueError` at initialization

Strict mode is intended for:

* CI
* Tests
* Environments where misconfiguration should halt execution immediately

---

## Logging Guarantees

* Logging cannot hang the main thread
* Filesystem failures do not crash the program
* Queue overflow drops logs rather than blocking
* Daily log files rotate automatically

This makes the library safe for:

* Network mounts
* Degraded disks
* Read-only filesystems
* systemd services
* Cron jobs

---

## Repository Layout

```
PythonEmailNotify/
├─ python_email_notify/
│  ├─ __init__.py
│  └─ pythonEmailNotify.py   # Canonical implementation
├─ README.md
├─ pyproject.toml
├─ LICENSE
├─ claude_tests/             # Portable validation & integration tests
└─ old/                      # Archived legacy versions
```

* `python_email_notify/pythonEmailNotify.py` is the **only source of truth**
* Root-level scripts are no longer used
* Package installs are reproducible and editable

---

## Production Readiness Statement

This library has been tested against:

* Invalid configuration
* Network failures
* SMTP failures
* TLS negotiation failures
* Logging failures
* Filesystem failures
* Concurrency and stress scenarios

It is suitable for production use **within its stated scope**.

---

## License

MIT License.

You may use, modify, and redistribute this library freely.

---

## Final Notes

This library is intentionally boring.

Predictable behavior under failure is the primary design goal.
If something goes wrong, you will know immediately — and your program will keep running.

That is the point.

