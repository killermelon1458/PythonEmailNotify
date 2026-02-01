"""
pythonEmailNotify.py

A lightweight, dependency-free email notification module + CLI for sending
plain text / HTML emails and exception reports over SMTP.

Design goals:
- Reliability / "bulletproof": no silent failures, deterministic exit codes in CLI
- User-friendly: explicit config resolution + actionable error messages
- Backwards compatible: EmailSender class + sendEmail/sendException preserved
- Dual-use: importable library AND CLI tool

Standard library only.
"""

from __future__ import annotations

import argparse
import email.utils
import logging
import os
import smtplib
import socket
import ssl
import sys
import time
import traceback
from dataclasses import dataclass
from email.message import EmailMessage
from typing import List, Optional, Sequence, Tuple, Union

# =========================
# Config defaults (edit here)
# =========================
DEFAULT_SMTP_SERVER: str = "smtp.gmail.com"
DEFAULT_SMTP_PORT: int = 587
DEFAULT_USE_TLS: bool = True          # STARTTLS (typically port 587)
DEFAULT_USE_SSL: bool = False         # SMTP over SSL (typically port 465)
DEFAULT_TIMEOUT_SECONDS: int = 10

# Environment variables (first match wins)
ENV_LOGIN_KEYS: Tuple[str, ...] = ("EMAIL_ADDRESS", "SMTP_LOGIN", "SMTP_USER")
ENV_PASSWORD_KEYS: Tuple[str, ...] = ("EMAIL_PASSWORD", "SMTP_PASSWORD", "SMTP_PASS")
ENV_DEFAULT_TO_KEYS: Tuple[str, ...] = ("MAIN_EMAIL_ADDRESS", "EMAIL_TO", "NOTIFY_TO")

# CLI default subject/body (only used if user doesn't provide)
DEFAULT_SUBJECT: str = "Notification"
DEFAULT_EXCEPTION_SUBJECT: str = "Exception Occurred in Script"

# =========================
# Exit codes (CLI)
# =========================
EXIT_OK = 0
EXIT_USER_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_AUTH_FAILURE = 3
EXIT_NETWORK_FAILURE = 4
EXIT_INTERNAL_ERROR = 5


# =========================
# Errors (library + CLI)
# =========================
class NotifierError(Exception):
    """Base class for notifier failures."""


class ConfigurationError(NotifierError):
    """Missing/invalid configuration."""


class AuthenticationError(NotifierError):
    """SMTP authentication failed."""


class NetworkError(NotifierError):
    """Network/connectivity problem."""


class SmtpError(NotifierError):
    """SMTP protocol/server problem."""


# =========================
# Utility helpers
# =========================
def _mask_secret(value: Optional[str], *, show: int = 2) -> str:
    if not value:
        return "<empty>"
    if len(value) <= show * 2:
        return "*" * len(value)
    return f"{value[:show]}{'*' * (len(value) - show * 2)}{value[-show:]}"


def _split_recipients(value: Union[str, Sequence[str], None]) -> List[str]:
    """
    Accept:
      - "a@b.com,c@d.com"
      - ["a@b.com", "c@d.com"]
      - None
    Returns a clean list.
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        raw = []
        for item in value:
            if item is None:
                continue
            raw.extend(str(item).split(","))
    else:
        raw = str(value).split(",")
    return [r.strip() for r in raw if r.strip()]


def _first_env(keys: Sequence[str]) -> Tuple[Optional[str], Optional[str]]:
    """Return (value, key_name) for first set env var, else (None, None)."""
    for k in keys:
        v = os.getenv(k)
        if v is not None and v != "":
            return v, k
    return None, None


def _is_interactive_stdin() -> bool:
    try:
        return sys.stdin.isatty()
    except Exception:
        return True


@dataclass
class ResolvedValue:
    value: Optional[object]
    source: str  # e.g., "cli --port", "env EMAIL_ADDRESS", "default", "explicit arg", "unset"


def _resolve(
    *,
    name: str,
    explicit: Optional[object],
    cli_value: Optional[object],
    env_keys: Optional[Sequence[str]],
    default: Optional[object],
    required: bool,
) -> ResolvedValue:
    """
    Resolution precedence:
      1) explicit (library constructor arg)
      2) cli_value (CLI only)
      3) env_keys
      4) default
    """
    if explicit is not None:
        return ResolvedValue(explicit, "explicit arg")
    if cli_value is not None:
        return ResolvedValue(cli_value, f"cli {name}")
    if env_keys:
        v, k = _first_env(env_keys)
        if v is not None:
            return ResolvedValue(v, f"env {k}")
    if default is not None:
        return ResolvedValue(default, "default")
    if required:
        return ResolvedValue(None, "missing (required)")
    return ResolvedValue(None, "unset")


def _coerce_int(name: str, value: object) -> int:
    try:
        return int(value)
    except Exception as e:
        raise ConfigurationError(f"{name} must be an integer; got {value!r}") from e


def _setup_logger(
    *,
    name: str = "pythonEmailNotify",
    verbose: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Avoid duplicate handlers if library imported multiple times.
    if not getattr(logger, "_pythonEmailNotify_configured", False):
        logger.propagate = False

        stream = logging.StreamHandler(stream=sys.stderr)
        stream.setLevel(logging.DEBUG if verbose else logging.INFO)
        stream.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
        logger.addHandler(stream)

        if log_file:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
            logger.addHandler(fh)

        logger._pythonEmailNotify_configured = True  # type: ignore[attr-defined]
        logger.debug("Logger configured (verbose=%s, log_file=%s)", verbose, log_file)

    # If log_file is newly requested later, add it if not present.
    if log_file and all(
        not (isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == os.path.abspath(log_file))
        for h in logger.handlers
    ):
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
        logger.addHandler(fh)
        logger.debug("Added log file handler: %s", log_file)

    return logger


def _classify_exception(exc: BaseException) -> Tuple[int, str]:
    """
    Map exceptions -> (exit_code, short_category).
    """
    if isinstance(exc, ConfigurationError):
        return EXIT_CONFIG_ERROR, "config"
    if isinstance(exc, AuthenticationError):
        return EXIT_AUTH_FAILURE, "auth"
    if isinstance(exc, NetworkError):
        return EXIT_NETWORK_FAILURE, "network"
    if isinstance(exc, SmtpError):
        return EXIT_NETWORK_FAILURE, "smtp"
    # smtplib exceptions classification
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return EXIT_AUTH_FAILURE, "auth"
    if isinstance(exc, (socket.gaierror, TimeoutError, socket.timeout, ConnectionError, OSError)):
        return EXIT_NETWORK_FAILURE, "network"
    if isinstance(exc, smtplib.SMTPException):
        return EXIT_NETWORK_FAILURE, "smtp"
    return EXIT_INTERNAL_ERROR, "internal"


# =========================
# Core library
# =========================
class EmailSender:
    """
    Backwards-compatible class.

    Legacy constructor (still supported):
        EmailSender(smtp_server, port, login, password, default_recipient=None)

    New optional kwargs:
        use_tls=True/False, use_ssl=True/False, timeout=seconds,
        verbose=True/False, log_file=path, raise_on_failure=True/False
    """

    def __init__(
        self,
        smtp_server: Optional[str],
        port: Optional[int],
        login: Optional[str],
        password: Optional[str],
        default_recipient: Optional[Union[str, Sequence[str]]] = None,
        *,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None,
        timeout: Optional[int] = None,
        verbose: bool = True,
        log_file: Optional[str] = None,
        raise_on_failure: bool = False,
    ):
        self.logger = _setup_logger(verbose=verbose, log_file=log_file)
        self.raise_on_failure = raise_on_failure
        self.last_error: Optional[BaseException] = None

        # Resolve config (explicit args only for library)
        rs = _resolve(name="--server", explicit=smtp_server, cli_value=None, env_keys=None, default=DEFAULT_SMTP_SERVER, required=True)
        rp = _resolve(name="--port", explicit=port, cli_value=None, env_keys=None, default=DEFAULT_SMTP_PORT, required=True)
        rl = _resolve(name="--login", explicit=login, cli_value=None, env_keys=ENV_LOGIN_KEYS, default=None, required=True)
        rpw = _resolve(name="--password", explicit=password, cli_value=None, env_keys=ENV_PASSWORD_KEYS, default=None, required=True)
        rto = _resolve(name="--to", explicit=default_recipient, cli_value=None, env_keys=ENV_DEFAULT_TO_KEYS, default=None, required=False)

        self.smtp_server = str(rs.value) if rs.value is not None else None
        self.port = _coerce_int("port", rp.value) if rp.value is not None else None
        self.login = str(rl.value) if rl.value is not None else None
        self.password = str(rpw.value) if rpw.value is not None else None
        self.default_recipient = ",".join(_split_recipients(rto.value)) if rto.value is not None else None

        self.use_tls = DEFAULT_USE_TLS if use_tls is None else bool(use_tls)
        self.use_ssl = DEFAULT_USE_SSL if use_ssl is None else bool(use_ssl)
        self.timeout = DEFAULT_TIMEOUT_SECONDS if timeout is None else int(timeout)

        # Emit explicit resolution summary
        self.logger.info("EmailSender configuration resolved:")
        self.logger.info("  SMTP server: %s (%s)", self.smtp_server, rs.source)
        self.logger.info("  Port: %s (%s)", self.port, rp.source)
        self.logger.info("  Login: %s (%s)", self.login or "<missing>", rl.source)
        self.logger.info("  Password: %s (%s)", _mask_secret(self.password), rpw.source)
        if self.default_recipient:
            self.logger.info("  Default recipient(s): %s (%s)", self.default_recipient, rto.source)
        else:
            self.logger.info("  Default recipient(s): <none> (%s)", rto.source)
        self.logger.info("  TLS (STARTTLS): %s", self.use_tls)
        self.logger.info("  SSL (SMTP_SSL): %s", self.use_ssl)
        self.logger.info("  Timeout: %ss", self.timeout)

        # Validate now (fail fast)
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        problems: List[str] = []

        if not self.smtp_server:
            problems.append("SMTP server is missing.")
        if self.port is None:
            problems.append("SMTP port is missing.")
        elif not (1 <= int(self.port) <= 65535):
            problems.append(f"SMTP port out of range: {self.port}")
        if not self.login:
            problems.append("SMTP login is missing. Provide login arg or set one of: " + ", ".join(ENV_LOGIN_KEYS))
        if not self.password:
            problems.append("SMTP password is missing. Provide password arg or set one of: " + ", ".join(ENV_PASSWORD_KEYS))

        if self.use_ssl and self.use_tls:
            problems.append("Both SSL and TLS are enabled. Choose one: use_ssl=True (465) OR use_tls=True (587).")

        if self.timeout <= 0:
            problems.append(f"timeout must be > 0 seconds; got {self.timeout}")

        if problems:
            msg = "Configuration error:\n  - " + "\n  - ".join(problems)
            self.logger.error(msg)
            raise ConfigurationError(msg)

    def sendEmail(
        self,
        subject: str,
        body: str,
        recipient: Optional[Union[str, Sequence[str]]] = None,
        html: bool = False,
        *,
        cc: Optional[Union[str, Sequence[str]]] = None,
        bcc: Optional[Union[str, Sequence[str]]] = None,
        reply_to: Optional[str] = None,
        dry_run: bool = False,
        raise_on_failure: Optional[bool] = None,
    ) -> bool:
        """
        Backwards-compatible signature + expanded options.

        Returns:
            True if sent (or dry_run), False on failure (unless raise_on_failure is True).
        """
        self.last_error = None
        rof = self.raise_on_failure if raise_on_failure is None else bool(raise_on_failure)

        to_list = _split_recipients(recipient) if recipient is not None else _split_recipients(self.default_recipient)
        cc_list = _split_recipients(cc)
        bcc_list = _split_recipients(bcc)

        if not to_list and not cc_list and not bcc_list:
            err = ConfigurationError(
                "Recipient is missing. Provide recipient argument OR set default_recipient OR set one of: "
                + ", ".join(ENV_DEFAULT_TO_KEYS)
            )
            self._handle_failure(err, rof)
            return False

        msg = EmailMessage()
        msg["From"] = self.login
        msg["To"] = ", ".join(to_list) if to_list else ""
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
        if reply_to:
            msg["Reply-To"] = reply_to
        msg["Subject"] = subject
        msg["Date"] = email.utils.formatdate(localtime=True)

        if html:
            msg.set_content("This message contains HTML. If you see this, your client does not render HTML.")
            msg.add_alternative(body, subtype="html")
        else:
            msg.set_content(body)

        all_recipients = to_list + cc_list + bcc_list

        self.logger.info("Preparing to send email:")
        self.logger.info("  From: %s", self.login)
        self.logger.info("  To: %s", ", ".join(to_list) if to_list else "<none>")
        self.logger.info("  Cc: %s", ", ".join(cc_list) if cc_list else "<none>")
        self.logger.info("  Bcc: %s", ", ".join(bcc_list) if bcc_list else "<none>")
        self.logger.info("  Subject: %s", subject)
        self.logger.info("  Body type: %s", "html" if html else "plain")
        self.logger.info("  SMTP: %s:%s | tls=%s ssl=%s timeout=%ss", self.smtp_server, self.port, self.use_tls, self.use_ssl, self.timeout)

        if dry_run:
            self.logger.warning("DRY RUN enabled: not sending email.")
            return True

        try:
            self._send_via_smtp(msg, all_recipients)
            self.logger.info("Email sent successfully.")
            return True
        except BaseException as exc:
            self._handle_failure(exc, rof)
            return False

    def _send_via_smtp(self, msg: EmailMessage, all_recipients: Sequence[str]) -> None:
        context = ssl.create_default_context()
        smtp_host = self.smtp_server or ""
        smtp_port = int(self.port or 0)

        if self.use_ssl:
            self.logger.debug("Opening SMTP_SSL connection...")
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=self.timeout, context=context) as server:
                server.set_debuglevel(0)
                self._login_and_send(server, msg, all_recipients)
        else:
            self.logger.debug("Opening SMTP connection...")
            with smtplib.SMTP(smtp_host, smtp_port, timeout=self.timeout) as server:
                server.set_debuglevel(0)
                server.ehlo()
                if self.use_tls:
                    self.logger.debug("Starting STARTTLS...")
                    server.starttls(context=context)
                    server.ehlo()
                self._login_and_send(server, msg, all_recipients)

    def _login_and_send(self, server: smtplib.SMTP, msg: EmailMessage, all_recipients: Sequence[str]) -> None:
        try:
            server.login(self.login or "", self.password or "")
        except smtplib.SMTPAuthenticationError as e:
            raise AuthenticationError(
                f"SMTP authentication failed for user {self.login!r}. "
                f"Server response: {getattr(e, 'smtp_error', b'').decode(errors='replace') or str(e)}"
            ) from e
        except smtplib.SMTPException as e:
            raise SmtpError(f"SMTP login failed: {e}") from e

        try:
            server.send_message(msg, to_addrs=list(all_recipients))
        except smtplib.SMTPRecipientsRefused as e:
            raise SmtpError(f"All recipients were refused: {e}") from e
        except smtplib.SMTPException as e:
            raise SmtpError(f"SMTP send failed: {e}") from e

    def _handle_failure(self, exc: BaseException, raise_on_failure: bool) -> None:
        self.last_error = exc

        if isinstance(exc, socket.gaierror):
            exc = NetworkError(f"DNS resolution failed for SMTP server {self.smtp_server!r}: {exc}")  # type: ignore[assignment]
        elif isinstance(exc, (socket.timeout, TimeoutError)):
            exc = NetworkError(f"SMTP connection timed out after {self.timeout}s to {self.smtp_server}:{self.port}: {exc}")  # type: ignore[assignment]
        elif isinstance(exc, smtplib.SMTPConnectError):
            exc = NetworkError(f"SMTP connect failed to {self.smtp_server}:{self.port}: {exc}")  # type: ignore[assignment]
        elif isinstance(exc, smtplib.SMTPServerDisconnected):
            exc = NetworkError(f"SMTP server disconnected unexpectedly: {exc}")  # type: ignore[assignment]
        elif isinstance(exc, ssl.SSLError):
            exc = NetworkError(f"TLS/SSL negotiation failed with {self.smtp_server}:{self.port}: {exc}")  # type: ignore[assignment]

        self.logger.error("Failed to send email.")
        self.logger.error("  Error type: %s", type(exc).__name__)
        self.logger.error("  Error: %s", exc)
        self.logger.error("  Config snapshot:")
        self.logger.error("    SMTP: %s:%s", self.smtp_server, self.port)
        self.logger.error("    login: %s", self.login or "<missing>")
        self.logger.error("    password: %s", _mask_secret(self.password))
        self.logger.error("    tls=%s ssl=%s timeout=%ss", self.use_tls, self.use_ssl, self.timeout)
        self.logger.debug("Full traceback:\n%s", traceback.format_exc())

        if raise_on_failure:
            raise exc

    def sendException(
        self,
        exception: BaseException,
        recipient: Optional[Union[str, Sequence[str]]] = None,
        *,
        subject: str = DEFAULT_EXCEPTION_SUBJECT,
        dry_run: bool = False,
        raise_on_failure: Optional[bool] = None,
    ) -> bool:
        try:
            tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        except Exception:
            tb = traceback.format_exc()

        body = (
            "<h1>Exception Report</h1>"
            f"<p><strong>Type:</strong> {type(exception).__name__}</p>"
            f"<p><strong>Message:</strong> {exception}</p>"
            "<p><strong>Traceback:</strong></p>"
            f"<pre>{tb}</pre>"
        )

        return self.sendEmail(
            subject=subject,
            body=body,
            recipient=recipient,
            html=True,
            dry_run=dry_run,
            raise_on_failure=raise_on_failure,
        )


def send_email(
    *,
    subject: str,
    message: str,
    to: Union[str, Sequence[str]],
    smtp_server: Optional[str] = None,
    port: Optional[int] = None,
    login: Optional[str] = None,
    password: Optional[str] = None,
    use_tls: Optional[bool] = None,
    use_ssl: Optional[bool] = None,
    timeout: Optional[int] = None,
    html: bool = False,
    cc: Optional[Union[str, Sequence[str]]] = None,
    bcc: Optional[Union[str, Sequence[str]]] = None,
    reply_to: Optional[str] = None,
    verbose: bool = True,
    log_file: Optional[str] = None,
    dry_run: bool = False,
    raise_on_failure: bool = False,
) -> bool:
    sender = EmailSender(
        smtp_server=smtp_server,
        port=port,
        login=login,
        password=password,
        default_recipient=None,
        use_tls=use_tls,
        use_ssl=use_ssl,
        timeout=timeout,
        verbose=verbose,
        log_file=log_file,
        raise_on_failure=raise_on_failure,
    )
    return sender.sendEmail(
        subject=subject,
        body=message,
        recipient=to,
        html=html,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        dry_run=dry_run,
    )


# =========================
# CLI
# =========================
def _cli_parse(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="pythonEmailNotify",
        description="Send SMTP email notifications (plain/HTML) or exception reports. Standard library only.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    p.add_argument("--server", dest="smtp_server", default=None, help="SMTP server hostname")
    p.add_argument("--port", dest="port", default=None, help="SMTP port (int)")
    p.add_argument("--tls", dest="use_tls", action="store_true", help="Enable STARTTLS (recommended for 587)")
    p.add_argument("--no-tls", dest="use_tls", action="store_false", help="Disable STARTTLS")
    p.set_defaults(use_tls=None)

    p.add_argument("--ssl", dest="use_ssl", action="store_true", help="Use SMTP over SSL (recommended for 465)")
    p.add_argument("--no-ssl", dest="use_ssl", action="store_false", help="Disable SMTP over SSL")
    p.set_defaults(use_ssl=None)

    p.add_argument("--timeout", dest="timeout", default=None, help="Timeout in seconds (int)")

    p.add_argument("--login", dest="login", default=None, help="SMTP login (email/username)")
    p.add_argument("--password", dest="password", default=None, help="SMTP password/app-password (CAUTION: visible in shell history)")
    p.add_argument("--password-env", dest="password_env", default=None, help="Name of env var containing password (safer than --password)")

    p.add_argument("--to", dest="to", action="append", default=None, help="Recipient(s). Repeatable or comma-separated.")
    p.add_argument("--cc", dest="cc", action="append", default=None, help="CC recipient(s). Repeatable or comma-separated.")
    p.add_argument("--bcc", dest="bcc", action="append", default=None, help="BCC recipient(s). Repeatable or comma-separated.")
    p.add_argument("--reply-to", dest="reply_to", default=None, help="Reply-To address")

    p.add_argument("--subject", dest="subject", default=None, help="Email subject")
    p.add_argument("--message", dest="message", default=None, help="Email body message")
    p.add_argument("--message-file", dest="message_file", default=None, help="Read body from a file path")
    p.add_argument("--html", dest="html", action="store_true", help="Treat message as HTML")
    p.add_argument("--plain", dest="html", action="store_false", help="Treat message as plain text")
    p.set_defaults(html=False)

    p.add_argument("--exception", dest="exception_mode", action="store_true", help="Wrap body as an exception report (HTML wrapper).")
    p.add_argument("--self-test", dest="self_test", action="store_true", help="Validate SMTP config (connect/auth). Optional send if --to is given.")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", help="Print what would happen, but do not send.")
    p.add_argument("--dump-config", dest="dump_config", action="store_true", help="Print resolved config snapshot and exit.")

    p.add_argument("--log-file", dest="log_file", default=None, help="Write logs to a file in addition to stderr.")
    p.add_argument("--quiet", dest="verbose", action="store_false", help="Less logging")
    p.add_argument("--verbose", dest="verbose", action="store_true", help="More logging")
    p.set_defaults(verbose=True)

    return p.parse_args(argv)


def _cli_resolve_and_run(ns: argparse.Namespace) -> int:
    logger = _setup_logger(verbose=ns.verbose, log_file=ns.log_file)

    cli_password = ns.password
    password_source = "cli --password" if cli_password is not None else None
    if cli_password is None and ns.password_env:
        v = os.getenv(ns.password_env)
        if v is None or v == "":
            logger.error("User error: --password-env %r was provided but that env var is not set or empty.", ns.password_env)
            return EXIT_USER_ERROR
        cli_password = v
        password_source = f"env {ns.password_env}"

    rs = _resolve(name="--server", explicit=None, cli_value=ns.smtp_server, env_keys=None, default=DEFAULT_SMTP_SERVER, required=True)
    rp = _resolve(name="--port", explicit=None, cli_value=ns.port, env_keys=None, default=DEFAULT_SMTP_PORT, required=True)
    rl = _resolve(name="--login", explicit=None, cli_value=ns.login, env_keys=ENV_LOGIN_KEYS, default=None, required=True)
    rpw = _resolve(name="--password", explicit=cli_password, cli_value=None, env_keys=ENV_PASSWORD_KEYS, default=None, required=True)
    rto = _resolve(name="--to", explicit=None, cli_value=ns.to, env_keys=ENV_DEFAULT_TO_KEYS, default=None, required=False)

    try:
        port = _coerce_int("port", rp.value) if rp.value is not None else None
        timeout = _coerce_int("timeout", ns.timeout) if ns.timeout is not None else None
    except ConfigurationError as e:
        logger.error(str(e))
        return EXIT_CONFIG_ERROR

    use_tls = DEFAULT_USE_TLS if ns.use_tls is None else bool(ns.use_tls)
    use_ssl = DEFAULT_USE_SSL if ns.use_ssl is None else bool(ns.use_ssl)

    if rs.source == "default":
        logger.info("No SMTP server given; using default %s", DEFAULT_SMTP_SERVER)
    if rp.source == "default":
        logger.info("No SMTP port given; using default %s", DEFAULT_SMTP_PORT)

    logger.info("CLI configuration resolved:")
    logger.info("  SMTP server: %s (%s)", rs.value, rs.source)
    logger.info("  Port: %s (%s)", port, rp.source)
    logger.info("  Login: %s (%s)", rl.value or "<missing>", rl.source)
    if password_source:
        logger.info("  Password: %s (%s)", _mask_secret(str(rpw.value) if rpw.value else None), password_source)
    else:
        logger.info("  Password: %s (%s)", _mask_secret(str(rpw.value) if rpw.value else None), rpw.source)

    to_list = _split_recipients(ns.to) if ns.to is not None else _split_recipients(rto.value)
    cc_list = _split_recipients(ns.cc)
    bcc_list = _split_recipients(ns.bcc)
    logger.info("  To: %s", ", ".join(to_list) if to_list else "<none>")
    logger.info("  Cc: %s", ", ".join(cc_list) if cc_list else "<none>")
    logger.info("  Bcc: %s", ", ".join(bcc_list) if bcc_list else "<none>")
    logger.info("  TLS (STARTTLS): %s", use_tls)
    logger.info("  SSL (SMTP_SSL): %s", use_ssl)
    logger.info("  Timeout: %ss", timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS)

    if ns.dump_config:
        logger.info("dump-config requested; exiting.")
        return EXIT_OK

    try:
        sender = EmailSender(
            smtp_server=str(rs.value) if rs.value is not None else None,
            port=port,
            login=str(rl.value) if rl.value is not None else None,
            password=str(rpw.value) if rpw.value is not None else None,
            default_recipient=",".join(to_list) if to_list else None,
            use_tls=use_tls,
            use_ssl=use_ssl,
            timeout=timeout,
            verbose=ns.verbose,
            log_file=ns.log_file,
            raise_on_failure=False,
        )
    except BaseException as e:
        code, _ = _classify_exception(e)
        logger.error("Failed to initialize EmailSender: %s", e)
        logger.debug("Traceback:\n%s", traceback.format_exc())
        return code

    if ns.self_test:
        logger.info("Self-test mode: validating connect/auth.")
        try:
            if to_list:
                ok = sender.sendEmail(
                    subject="pythonEmailNotify self-test",
                    body="Self-test: SMTP connect/auth/send succeeded.",
                    recipient=to_list,
                    html=False,
                    dry_run=ns.dry_run,
                )
            else:
                if sender.use_ssl:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(sender.smtp_server, int(sender.port), timeout=sender.timeout, context=context) as s:
                        s.login(sender.login or "", sender.password or "")
                else:
                    with smtplib.SMTP(sender.smtp_server, int(sender.port), timeout=sender.timeout) as s:
                        s.ehlo()
                        if sender.use_tls:
                            context = ssl.create_default_context()
                            s.starttls(context=context)
                            s.ehlo()
                        s.login(sender.login or "", sender.password or "")
                ok = True
                logger.info("Self-test connect/auth succeeded. (No email sent because no --to provided.)")

            return EXIT_OK if ok else EXIT_NETWORK_FAILURE
        except BaseException as e:
            code, _ = _classify_exception(e)
            logger.error("Self-test failed: %s", e)
            logger.debug("Traceback:\n%s", traceback.format_exc())
            return code

    subject = ns.subject or DEFAULT_SUBJECT

    body: Optional[str] = None
    if ns.message_file:
        try:
            with open(ns.message_file, "r", encoding="utf-8") as f:
                body = f.read()
            logger.info("Loaded message body from file: %s", ns.message_file)
        except Exception as e:
            logger.error("User error: failed to read --message-file %r: %s", ns.message_file, e)
            return EXIT_USER_ERROR
    elif ns.message is not None:
        body = ns.message
    else:
        if not _is_interactive_stdin():
            body = sys.stdin.read()
            logger.info("Loaded message body from stdin (piped input).")
        else:
            logger.error("User error: no message provided. Use --message, --message-file, or pipe stdin.")
            return EXIT_USER_ERROR

    if ns.exception_mode:
        logger.info("--exception mode enabled: wrapping body as exception report.")
        report_html = (
            "<h1>Exception Report (CLI)</h1>"
            "<p><strong>Type:</strong> RuntimeError</p>"
            "<p><strong>Message:</strong> Exception report (CLI)</p>"
            "<p><strong>Traceback:</strong></p>"
            f"<pre>{body}</pre>"
        )
        ok = sender.sendEmail(
            subject=ns.subject or DEFAULT_EXCEPTION_SUBJECT,
            body=report_html,
            recipient=to_list or sender.default_recipient,
            html=True,
            cc=cc_list,
            bcc=bcc_list,
            reply_to=ns.reply_to,
            dry_run=ns.dry_run,
        )
    else:
        ok = sender.sendEmail(
            subject=subject,
            body=body,
            recipient=to_list or sender.default_recipient,
            html=bool(ns.html),
            cc=cc_list,
            bcc=bcc_list,
            reply_to=ns.reply_to,
            dry_run=ns.dry_run,
        )

    return EXIT_OK if ok else EXIT_NETWORK_FAILURE


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        ns = _cli_parse(argv)
        return _cli_resolve_and_run(ns)
    except SystemExit:
        raise
    except BaseException as e:
        logger = _setup_logger(verbose=True, log_file=None)
        code, _ = _classify_exception(e)
        logger.error("Internal error: %s", e)
        logger.error("Traceback:\n%s", traceback.format_exc())
        return code


if __name__ == "__main__":
    raise SystemExit(main())
