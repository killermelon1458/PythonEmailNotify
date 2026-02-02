# pythonEmailNotify.py
import os
import sys
import time
import smtplib
import traceback
import threading
import queue
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# CONFIGURATION
# =========================

ENABLE_LOGGING = True

# If True: invalid init config raises ValueError (stricter, potentially breaking).
# If False (default): print loud diagnostics, mark sender invalid, and fail sends loudly.
STRICT_CONFIG_VALIDATION = False

DEFAULT_LOG_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_LOG_DIR = ""  # empty = disabled
LOG_DIR = CUSTOM_LOG_DIR or DEFAULT_LOG_DIR

SMTP_TIMEOUT_SECONDS = 10  # Hard timeout to prevent hangs

# Logging queue config (prevents main thread hangs)
_LOG_QUEUE_MAX = 1000
_LOG_THREAD_NAME = "pythonEmailNotify-log-writer"

# =========================
# LOUD OUTPUT (never trust stderr)
# =========================

def _now():
    # Separate helper so we can guard it independently.
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "0000-00-00 00:00:00"

def _loud_print(message: str):
    # Printing can fail (closed stderr, broken pipe). Never let that crash the program.
    try:
        stream = sys.stderr if getattr(sys, "stderr", None) else sys.__stderr__
        print(f"[pythonEmailNotify] {_now()} | {message}", file=stream, flush=True)
    except Exception:
        # Last resort: swallow
        pass

# =========================
# NON-BLOCKING LOGGING
# =========================

_log_q = queue.Queue(maxsize=_LOG_QUEUE_MAX)
_log_thread_started = False
_log_drop_count = 0
_log_drop_last_notice = 0

def _current_log_path() -> str:
    # True daily log rotation even for long-running processes.
    date_str = time.strftime("%Y-%m-%d")
    return os.path.join(LOG_DIR, f"pythonEmailNotify_{date_str}.log")

def _ensure_log_dir_best_effort():
    # Best-effort directory creation; must never raise.
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception as e:
        _loud_print(f"LOG DIR CREATION FAILED: {e}")

def _log_worker():
    # Daemon thread: can hang without affecting the main program.
    while True:
        try:
            line = _log_q.get()
            if line is None:
                return
            path = _current_log_path()

            # Directory might be deleted after startup; best-effort recreate.
            _ensure_log_dir_best_effort()

            # This can still block on pathological FS, but it's in a daemon thread.
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            _loud_print(f"LOGGING FAILURE (writer thread): {e}")
        finally:
            try:
                _log_q.task_done()
            except Exception:
                pass

def _start_logging_once():
    global _log_thread_started
    if _log_thread_started:
        return
    _log_thread_started = True

    _ensure_log_dir_best_effort()

    try:
        t = threading.Thread(target=_log_worker, name=_LOG_THREAD_NAME, daemon=True)
        t.start()
    except Exception as e:
        _loud_print(f"FAILED to start log writer thread: {e}")

def _safe_log(message: str):
    # Absolutely must not hang the caller.
    global _log_drop_count, _log_drop_last_notice

    if not ENABLE_LOGGING:
        return

    if not _log_thread_started:
        _start_logging_once()

    # Build the final line outside of the writer thread; keep it simple.
    line = f"{_now()} | {message}"

    try:
        _log_q.put_nowait(line)
    except queue.Full:
        _log_drop_count += 1
        # Don't spam; report occasionally.
        if _log_drop_count - _log_drop_last_notice >= 50:
            _log_drop_last_notice = _log_drop_count
            _loud_print(f"LOG QUEUE FULL: dropped {_log_drop_count} log lines")

# =========================
# CORE CLASS
# =========================

class EmailSender:
    def __init__(self, smtp_server, port, login, password, default_recipient=None):
        self.smtp_server = smtp_server
        self.port = port
        self.login = login
        self.password = password
        self.default_recipient = default_recipient
        self._config_valid = True

        errors = []

        # SMTP server
        if smtp_server is None or smtp_server == "":
            errors.append("SMTP server is missing or empty")
        elif not isinstance(smtp_server, str):
            errors.append(f"SMTP server must be a string, got {type(smtp_server).__name__}")
        elif smtp_server.strip() == "":
            errors.append("SMTP server is whitespace only")

        # Port
        if port is None or port == "":
            errors.append("Port is missing or empty")
        else:
            try:
                port_int = int(port)
                if port_int < 1 or port_int > 65535:
                    errors.append(f"Port {port_int} is outside valid range (1-65535)")
            except (ValueError, TypeError):
                errors.append(f"Port must be a number, got '{port}' ({type(port).__name__})")

        # Login
        if login is None or login == "":
            errors.append("Login/username is missing or empty")
        elif not isinstance(login, str):
            errors.append(f"Login must be a string, got {type(login).__name__}")
        elif login.strip() == "":
            errors.append("Login is whitespace only")

        # Password
        if password is None or password == "":
            errors.append("Password is missing or empty")
        elif not isinstance(password, str):
            errors.append(f"Password must be a string, got {type(password).__name__}")
        elif password.strip() == "":
            errors.append("Password is whitespace only")

        # default_recipient (optional)
        if default_recipient is not None:
            if not isinstance(default_recipient, str):
                errors.append(f"Default recipient must be a string, got {type(default_recipient).__name__}")
            elif default_recipient.strip() == "":
                errors.append("Default recipient is whitespace only")
            elif "@" not in default_recipient:
                errors.append(f"Default recipient '{default_recipient}' doesn't look like an email (missing @)")

        if errors:
            self._config_valid = False
            header = "EmailSender initialization DIAGNOSTICS:"
            _loud_print(header)
            _safe_log(header)

            for i, err in enumerate(errors, 1):
                line = f"  {i}. {err}"
                _loud_print(line)
                _safe_log(line)

            # Helpful env hint (non-authoritative)
            hint = "Hint: if you use env vars in your calling script, verify they are set."
            _loud_print(hint)
            _safe_log(hint)

            if STRICT_CONFIG_VALIDATION:
                raise ValueError(f"{len(errors)} validation error(s) - see stderr for details")

        # Normalize where safe (don’t strip password)
        try:
            self.smtp_server = self.smtp_server.strip() if isinstance(self.smtp_server, str) else self.smtp_server
        except Exception:
            pass
        try:
            self.login = self.login.strip() if isinstance(self.login, str) else self.login
        except Exception:
            pass
        try:
            self.default_recipient = self.default_recipient.strip() if isinstance(self.default_recipient, str) else self.default_recipient
        except Exception:
            pass
        try:
            self.port = int(self.port) if self.port is not None and self.port != "" else self.port
        except Exception:
            pass

        _safe_log("EmailSender initialized")

    def sendEmail(self, subject, body, recipient=None, html=False):
        # Return a status boolean; safe addition (doesn't break callers who ignore return).
        # Only raise where the original code already did (missing recipient).
        
        # Validate recipient parameter first (before using default)
        if recipient is not None:
            if not isinstance(recipient, str) or recipient.strip() == "":
                _loud_print(f"INVALID RECIPIENT: {recipient!r}")
                _safe_log("Invalid recipient")
                return False
        
        # Now handle None recipient - use default or raise
        if recipient is None:
            if self.default_recipient is None:
                msg = "Recipient email must be specified"
                _loud_print(msg)
                _safe_log(msg)
                raise ValueError(msg)
            recipient = self.default_recipient
        
        # If init config is bad, fail loudly and fast (but don't raise by default).
        if not self._config_valid:
            _loud_print("SEND ABORTED: EmailSender config invalid (see init diagnostics above)")
            _safe_log("Send aborted due to invalid config")
            return False
        
        # Subject/body safety
        try:
            subject = "" if subject is None else str(subject)
        except Exception:
            subject = "pythonEmailNotify: (subject conversion failed)"
            _loud_print("WARNING: subject conversion failed; using fallback")
        try:
            body = "" if body is None else str(body)
        except Exception:
            body = "pythonEmailNotify: (body conversion failed)"
            _loud_print("WARNING: body conversion failed; using fallback")
        
        # Construct email
        try:
            msg = MIMEMultipart()
            msg["From"] = str(self.login)
            msg["To"] = recipient.strip()
            msg["Subject"] = subject
            subtype = "html" if bool(html) else "plain"
            msg.attach(MIMEText(body, subtype))
        except Exception:
            _loud_print("FAILED to construct email message")
            _loud_print(traceback.format_exc())
            _safe_log("Message construction failure")
            return False
        
        # Send
        try:
            _safe_log(f"Connecting to SMTP {self.smtp_server}:{self.port}")
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.port, timeout=SMTP_TIMEOUT_SECONDS) as server:
                # Explicit EHLO helps with some servers; harmless otherwise.
                try:
                    server.ehlo()
                except Exception:
                    pass
                server.starttls(context=context)
                try:
                    server.ehlo()
                except Exception:
                    pass
                server.login(self.login, self.password)
                server.send_message(msg)
            _loud_print(f"Email sent to {recipient.strip()}")
            _safe_log(f"Email sent to {recipient.strip()}")
            return True
        except Exception:
            _loud_print("SMTP SEND FAILURE")
            _loud_print(traceback.format_exc())
            _safe_log("SMTP send failure")
            return False
    def sendException(self, exception, recipient=None):
        # Return status boolean (safe addition).
        try:
            ex_type = type(exception).__name__ if exception is not None else "UnknownException"
            ex_msg = str(exception) if exception is not None else "(no exception object)"

            # Use the exception's own traceback if present; don't rely on "current except" context.
            if exception is not None and getattr(exception, "__traceback__", None) is not None:
                tb_text = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            else:
                tb_text = traceback.format_exc()

            subject = "Exception Occurred in Script"
            body = (
                "<h1>Exception Report</h1>"
                f"<p><strong>Type:</strong> {ex_type}</p>"
                f"<p><strong>Message:</strong> {ex_msg}</p>"
                "<p><strong>Traceback:</strong></p>"
                f"<pre>{tb_text}</pre>"
            )
            return self.sendEmail(subject, body, recipient, html=True)

        except Exception:
            _loud_print("FAILED while sending exception report")
            _loud_print(traceback.format_exc())
            _safe_log("sendException failure")
            return False
