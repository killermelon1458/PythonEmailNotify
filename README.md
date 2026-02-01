# pythonEmailNotify

A hardened, dependency-free Python utility for sending **reliable, non-blocking email notifications** from scripts, services, and infrastructure tooling.

This library is designed for **production environments** where failures must be **loud**, logging must **never hang**, and email delivery attempts must be **predictable and observable**.

---

## Key Properties

* **Fail-loud by design**

  * All failures are printed to `stderr` with timestamps
  * No silent errors
  * Clear diagnostics for misconfiguration and runtime failures

* **Non-blocking logging**

  * Logging is optional
  * Logging cannot block or hang the calling process
  * Filesystem or disk failures never stop execution

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

* Systemd `OnFailure=` hooks
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

This project is intentionally distributed as a **single Python file**.

```bash
# Copy directly into your project
cp pythonEmailNotify.py /path/to/your/project/
```

Or vendor it into your repository.

---

## Basic Usage

```python
from pythonEmailNotify import EmailSender

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

Return value:

* `True` → email send attempt succeeded
* `False` → failure occurred (details printed to stderr)

---

## Environment Variable Pattern (Recommended)

Many users inject credentials via environment variables:

```bash
EMAIL_ADDRESS=sender@example.com
EMAIL_PASSWORD=app_password
MAIN_EMAIL_ADDRESS=alerts@example.com
```

```python
import os
from pythonEmailNotify import EmailSender

sender = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    login=os.getenv("EMAIL_ADDRESS"),
    password=os.getenv("EMAIL_PASSWORD"),
    default_recipient=os.getenv("MAIN_EMAIL_ADDRESS"),
)
```

If variables are missing or invalid, the library prints **explicit diagnostics**.

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
* Works even when called outside the original `except` block
* Does not crash if email sending fails

---

## Configuration Options

### Logging

```python
ENABLE_LOGGING = False  # default
```

When enabled:

* Logs are written to daily rotating files
* Logging is asynchronous and non-blocking
* Logging failures are printed but never fatal

### Strict Validation

```python
STRICT_CONFIG_VALIDATION = False  # default
```

* `False` (default): invalid configuration prints diagnostics and fails sends loudly
* `True`: invalid configuration raises `ValueError` at initialization

Use strict mode when misconfiguration should halt execution immediately.

---

## Logging Behavior (Guarantees)

* Logging cannot hang the main thread
* Filesystem issues do not crash the program
* Queue overflow drops logs rather than blocking
* Daily log files rotate automatically

This makes the library safe for:

* Network mounts
* Degraded disks
* Read-only filesystems
* Headless environments

---

## Testing

This repository includes:

* **Unit tests** (deterministic, mock-based)
* **Integration tests** (real SMTP, opt-in)
* **Smoke tests** (environment validation + real send)
* **Stress tests** (manual, non-CI)

### Run unit tests

```bash
python -m unittest -v
```

### Run integration test (explicit opt-in)

```bash
export PYTHON_EMAIL_NOTIFY_RUN_INTEGRATION=1
python -m unittest -v
```

### Smoke test

```bash
python smoke_test.py
```

---

## Repository Layout

```
pythonEmailNotify/
├─ pythonEmailNotify.py     # Canonical production library
├─ README.md
├─ .gitignore
├─ claude_tests/            # Portable validation & integration tests
└─ old/                     # Archived legacy versions
```

* `pythonEmailNotify.py` at root is authoritative
* `old/` preserves historical versions for reference
* `claude_tests/` is intentionally tracked for cross-machine validation

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
