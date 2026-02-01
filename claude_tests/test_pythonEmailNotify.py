#!/usr/bin/env python3
"""
Production-Grade Test Suite for pythonEmailNotify.py

This test suite attempts to break every aspect of the email notification system:
- Configuration validation
- Network failure scenarios
- Invalid inputs
- Edge cases
- Threading/logging behavior
- SMTP protocol handling

Each test sends an email with a unique subject so you can verify delivery.
"""

import os
import sys
import time
import unittest
import threading
import tempfile
import shutil
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

# Import the module under test
import pythonEmailNotify
from pythonEmailNotify import EmailSender

# Test configuration from environment
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
MAIN_EMAIL_ADDRESS = os.getenv("MAIN_EMAIL_ADDRESS")

# Verify environment variables are set
if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, MAIN_EMAIL_ADDRESS]):
    print("ERROR: Required environment variables not set:", file=sys.stderr)
    print("  EMAIL_ADDRESS:", "✓" if EMAIL_ADDRESS else "✗", file=sys.stderr)
    print("  EMAIL_PASSWORD:", "✓" if EMAIL_PASSWORD else "✗", file=sys.stderr)
    print("  MAIN_EMAIL_ADDRESS:", "✓" if MAIN_EMAIL_ADDRESS else "✗", file=sys.stderr)
    sys.exit(1)


class TestConfigurationValidation(unittest.TestCase):
    """Test all configuration validation scenarios"""

    def setUp(self):
        """Reset strict validation before each test"""
        pythonEmailNotify.STRICT_CONFIG_VALIDATION = False
        pythonEmailNotify.ENABLE_LOGGING = True

    def test_01_valid_configuration(self):
        """TEST 01: Valid configuration should initialize successfully"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        self.assertTrue(sender._config_valid)
        
        # Send confirmation email
        result = sender.sendEmail(
            subject="TEST 01: Valid Configuration ✓",
            body="This test validates that a properly configured EmailSender works correctly."
        )
        self.assertTrue(result)

    def test_02_missing_smtp_server(self):
        """TEST 02: Missing SMTP server should fail validation"""
        sender = EmailSender(
            smtp_server=None,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_03_empty_smtp_server(self):
        """TEST 03: Empty SMTP server should fail validation"""
        sender = EmailSender(
            smtp_server="",
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_04_whitespace_smtp_server(self):
        """TEST 04: Whitespace-only SMTP server should fail validation"""
        sender = EmailSender(
            smtp_server="   ",
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_05_invalid_smtp_type(self):
        """TEST 05: Non-string SMTP server should fail validation"""
        sender = EmailSender(
            smtp_server=12345,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_06_missing_port(self):
        """TEST 06: Missing port should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=None,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_07_empty_port(self):
        """TEST 07: Empty port should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port="",
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_08_invalid_port_type(self):
        """TEST 08: Non-numeric port should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port="abc",
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_09_port_out_of_range_low(self):
        """TEST 09: Port below valid range should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=0,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_10_port_out_of_range_high(self):
        """TEST 10: Port above valid range should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=65536,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_11_missing_login(self):
        """TEST 11: Missing login should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=None,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_12_empty_login(self):
        """TEST 12: Empty login should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login="",
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_13_whitespace_login(self):
        """TEST 13: Whitespace-only login should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login="   ",
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_14_invalid_login_type(self):
        """TEST 14: Non-string login should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=12345,
            password=EMAIL_PASSWORD
        )
        self.assertFalse(sender._config_valid)

    def test_15_missing_password(self):
        """TEST 15: Missing password should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=None
        )
        self.assertFalse(sender._config_valid)

    def test_16_empty_password(self):
        """TEST 16: Empty password should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=""
        )
        self.assertFalse(sender._config_valid)

    def test_17_whitespace_password(self):
        """TEST 17: Whitespace-only password should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password="   "
        )
        self.assertFalse(sender._config_valid)

    def test_18_invalid_password_type(self):
        """TEST 18: Non-string password should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=12345
        )
        self.assertFalse(sender._config_valid)

    def test_19_invalid_default_recipient_type(self):
        """TEST 19: Non-string default recipient should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=12345
        )
        self.assertFalse(sender._config_valid)

    def test_20_whitespace_default_recipient(self):
        """TEST 20: Whitespace-only default recipient should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient="   "
        )
        self.assertFalse(sender._config_valid)

    def test_21_invalid_email_format(self):
        """TEST 21: Default recipient without @ should fail validation"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient="notanemail"
        )
        self.assertFalse(sender._config_valid)

    def test_22_multiple_validation_errors(self):
        """TEST 22: Multiple validation errors should all be reported"""
        sender = EmailSender(
            smtp_server="",
            port="invalid",
            login=None,
            password=""
        )
        self.assertFalse(sender._config_valid)

    def test_23_strict_mode_raises_exception(self):
        """TEST 23: Strict mode should raise ValueError on invalid config"""
        pythonEmailNotify.STRICT_CONFIG_VALIDATION = True
        with self.assertRaises(ValueError):
            EmailSender(
                smtp_server=None,
                port=SMTP_PORT,
                login=EMAIL_ADDRESS,
                password=EMAIL_PASSWORD
            )

    def test_24_invalid_config_prevents_send(self):
        """TEST 24: Invalid configuration should prevent email sending"""
        sender = EmailSender(
            smtp_server=None,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        result = sender.sendEmail(
            subject="This should not send",
            body="Invalid config should block this"
        )
        self.assertFalse(result)


class TestEmailSending(unittest.TestCase):
    """Test email sending functionality"""

    def setUp(self):
        """Create valid sender for each test"""
        pythonEmailNotify.ENABLE_LOGGING = False
        self.sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )

    def test_25_send_plain_text_email(self):
        """TEST 25: Send plain text email"""
        result = self.sender.sendEmail(
            subject="TEST 25: Plain Text Email ✓",
            body="This is a plain text email body.",
            html=False
        )
        self.assertTrue(result)
        time.sleep(0.5)  # Rate limiting

    def test_26_send_html_email(self):
        """TEST 26: Send HTML email"""
        result = self.sender.sendEmail(
            subject="TEST 26: HTML Email ✓",
            body="<h1>HTML Header</h1><p>This is an <strong>HTML</strong> email.</p>",
            html=True
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_27_use_default_recipient(self):
        """TEST 27: Use default recipient when none specified"""
        result = self.sender.sendEmail(
            subject="TEST 27: Default Recipient ✓",
            body="This should go to the default recipient."
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_28_override_default_recipient(self):
        """TEST 28: Override default recipient"""
        result = self.sender.sendEmail(
            subject="TEST 28: Override Recipient ✓",
            body="This overrides the default recipient.",
            recipient=MAIN_EMAIL_ADDRESS
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_29_missing_recipient_raises_error(self):
        """TEST 29: Missing recipient with no default should raise ValueError"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=None
        )
        with self.assertRaises(ValueError):
            sender.sendEmail(
                subject="This should fail",
                body="No recipient specified"
            )

    def test_30_empty_subject(self):
        """TEST 30: Empty subject should still send"""
        result = self.sender.sendEmail(
            subject="",
            body="TEST 30: This email has an empty subject."
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_31_none_subject(self):
        """TEST 31: None subject should convert to empty string"""
        result = self.sender.sendEmail(
            subject=None,
            body="TEST 31: This email had a None subject."
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_32_empty_body(self):
        """TEST 32: Empty body should still send"""
        result = self.sender.sendEmail(
            subject="TEST 32: Empty Body ✓",
            body=""
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_33_none_body(self):
        """TEST 33: None body should convert to empty string"""
        result = self.sender.sendEmail(
            subject="TEST 33: None Body ✓",
            body=None
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_34_unicode_subject(self):
        """TEST 34: Unicode characters in subject"""
        result = self.sender.sendEmail(
            subject="TEST 34: Unicode ✓ 你好 🎉 العربية",
            body="Unicode test in subject line"
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_35_unicode_body(self):
        """TEST 35: Unicode characters in body"""
        result = self.sender.sendEmail(
            subject="TEST 35: Unicode Body ✓",
            body="Unicode test: 你好世界 🎉 مرحبا Привет"
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_36_long_subject(self):
        """TEST 36: Very long subject line"""
        long_subject = "TEST 36: " + "A" * 500
        result = self.sender.sendEmail(
            subject=long_subject,
            body="Testing very long subject line"
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_37_long_body(self):
        """TEST 37: Very long email body"""
        long_body = "TEST 37: Long body test\n" + ("X" * 10000)
        result = self.sender.sendEmail(
            subject="TEST 37: Long Body ✓",
            body=long_body
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_38_special_characters_subject(self):
        """TEST 38: Special characters in subject"""
        result = self.sender.sendEmail(
            subject="TEST 38: Special <>&\"'\\/ chars ✓",
            body="Testing special characters in subject"
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_39_newlines_in_subject(self):
        """TEST 39: Newlines in subject (should be handled by MIME)"""
        result = self.sender.sendEmail(
            subject="TEST 39: Subject\nwith\nnewlines ✓",
            body="Testing newlines in subject"
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_40_multiline_body(self):
        """TEST 40: Multiline body"""
        result = self.sender.sendEmail(
            subject="TEST 40: Multiline Body ✓",
            body="Line 1\nLine 2\nLine 3\n\nLine 5 (skipped 4)"
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_41_html_with_scripts(self):
        """TEST 41: HTML with script tags (should be sent as-is)"""
        result = self.sender.sendEmail(
            subject="TEST 41: HTML with Scripts ✓",
            body="<script>alert('test');</script><p>HTML with script tag</p>",
            html=True
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_42_invalid_recipient_format(self):
        """TEST 42: Invalid recipient format should fail"""
        result = self.sender.sendEmail(
            subject="Should not send",
            body="Invalid recipient",
            recipient=""
        )
        self.assertFalse(result)

    def test_43_whitespace_recipient(self):
        """TEST 43: Whitespace-only recipient should fail"""
        result = self.sender.sendEmail(
            subject="Should not send",
            body="Whitespace recipient",
            recipient="   "
        )
        self.assertFalse(result)

    def test_44_non_string_recipient(self):
        """TEST 44: Non-string recipient should fail"""
        result = self.sender.sendEmail(
            subject="Should not send",
            body="Non-string recipient",
            recipient=12345
        )
        self.assertFalse(result)

    def test_45_rapid_succession_sends(self):
        """TEST 45: Multiple emails in rapid succession"""
        results = []
        for i in range(5):
            result = self.sender.sendEmail(
                subject=f"TEST 45: Rapid Send {i+1}/5 ✓",
                body=f"Rapid fire email #{i+1}"
            )
            results.append(result)
            time.sleep(0.3)  # Small delay to avoid rate limiting
        
        self.assertTrue(all(results))


class TestExceptionHandling(unittest.TestCase):
    """Test exception sending functionality"""

    def setUp(self):
        """Create valid sender for each test"""
        pythonEmailNotify.ENABLE_LOGGING = False
        self.sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )

    def test_46_send_simple_exception(self):
        """TEST 46: Send simple exception"""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            result = self.sender.sendException(e)
            self.assertTrue(result)
            time.sleep(0.5)

    def test_47_send_exception_with_traceback(self):
        """TEST 47: Send exception with full traceback"""
        try:
            def inner():
                def deeper():
                    raise RuntimeError("Deep exception")
                deeper()
            inner()
        except RuntimeError as e:
            result = self.sender.sendException(e)
            self.assertTrue(result)
            time.sleep(0.5)

    def test_48_send_none_exception(self):
        """TEST 48: Send None as exception (edge case)"""
        result = self.sender.sendException(None)
        self.assertTrue(result)
        time.sleep(0.5)

    def test_49_send_exception_with_unicode(self):
        """TEST 49: Exception with Unicode message"""
        try:
            raise Exception("Unicode error: 你好 🎉")
        except Exception as e:
            result = self.sender.sendException(e)
            self.assertTrue(result)
            time.sleep(0.5)

    def test_50_send_exception_override_recipient(self):
        """TEST 50: Send exception to different recipient"""
        try:
            raise Exception("Test exception to specific recipient")
        except Exception as e:
            result = self.sender.sendException(e, recipient=MAIN_EMAIL_ADDRESS)
            self.assertTrue(result)
            time.sleep(0.5)


class TestNetworkFailures(unittest.TestCase):
    """Test network failure scenarios"""

    def setUp(self):
        """Setup for network tests"""
        pythonEmailNotify.ENABLE_LOGGING = False

    def test_51_invalid_smtp_server(self):
        """TEST 51: Invalid SMTP server should fail gracefully"""
        sender = EmailSender(
            smtp_server="invalid.smtp.server.that.does.not.exist.com",
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        result = sender.sendEmail(
            subject="Should not send",
            body="Invalid SMTP server"
        )
        self.assertFalse(result)

    def test_52_invalid_port(self):
        """TEST 52: Invalid port should fail gracefully"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=12345,  # Wrong port
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        result = sender.sendEmail(
            subject="Should not send",
            body="Invalid port"
        )
        self.assertFalse(result)

    def test_53_wrong_credentials(self):
        """TEST 53: Wrong credentials should fail gracefully"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password="wrong_password_123",
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        result = sender.sendEmail(
            subject="Should not send",
            body="Wrong password"
        )
        self.assertFalse(result)

    def test_54_timeout_handling(self):
        """TEST 54: Timeout should be handled (using invalid server)"""
        # This should timeout per SMTP_TIMEOUT_SECONDS
        sender = EmailSender(
            smtp_server="10.255.255.1",  # Non-routable IP
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        start = time.time()
        result = sender.sendEmail(
            subject="Should not send",
            body="Testing timeout"
        )
        elapsed = time.time() - start
        
        self.assertFalse(result)
        # Should timeout within reasonable time (SMTP_TIMEOUT_SECONDS + overhead)
        self.assertLess(elapsed, 20)


class TestLoggingSystem(unittest.TestCase):
    """Test logging functionality"""

    def setUp(self):
        """Setup temporary log directory"""
        self.temp_log_dir = tempfile.mkdtemp()
        self.original_log_dir = pythonEmailNotify.LOG_DIR
        pythonEmailNotify.LOG_DIR = self.temp_log_dir
        pythonEmailNotify.ENABLE_LOGGING = True
        pythonEmailNotify._log_thread_started = False

    def tearDown(self):
        """Cleanup temporary log directory"""
        pythonEmailNotify.LOG_DIR = self.original_log_dir
        pythonEmailNotify.ENABLE_LOGGING = False
        if os.path.exists(self.temp_log_dir):
            shutil.rmtree(self.temp_log_dir)

    def test_55_logging_enabled(self):
        """TEST 55: Logging should create log files"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        sender.sendEmail(
            subject="TEST 55: Logging Test ✓",
            body="Testing that logging works"
        )
        time.sleep(1)  # Wait for log thread to write
        
        # Check if log file was created
        log_files = os.listdir(self.temp_log_dir)
        self.assertGreater(len(log_files), 0)
        time.sleep(0.5)

    def test_56_logging_disabled(self):
        """TEST 56: Logging disabled should not create files"""
        pythonEmailNotify.ENABLE_LOGGING = False
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        sender.sendEmail(
            subject="TEST 56: No Logging ✓",
            body="Testing with logging disabled"
        )
        time.sleep(1)
        
        # No log files should be created
        log_files = os.listdir(self.temp_log_dir)
        self.assertEqual(len(log_files), 0)
        time.sleep(0.5)


class TestEdgeCases(unittest.TestCase):
    """Test various edge cases and corner scenarios"""

    def setUp(self):
        """Create valid sender for each test"""
        pythonEmailNotify.ENABLE_LOGGING = False
        self.sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )

    def test_57_recipient_with_whitespace(self):
        """TEST 57: Recipient with surrounding whitespace should be trimmed"""
        result = self.sender.sendEmail(
            subject="TEST 57: Whitespace Trim ✓",
            body="Recipient had surrounding whitespace",
            recipient=f"  {MAIN_EMAIL_ADDRESS}  "
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_58_port_as_string(self):
        """TEST 58: Port as string should be converted to int"""
        sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port="587",  # String instead of int
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        result = sender.sendEmail(
            subject="TEST 58: String Port ✓",
            body="Port was provided as string"
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_59_integer_subject(self):
        """TEST 59: Integer subject should be converted to string"""
        result = self.sender.sendEmail(
            subject=12345,
            body="TEST 59: Integer subject was converted to string"
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_60_integer_body(self):
        """TEST 60: Integer body should be converted to string"""
        result = self.sender.sendEmail(
            subject="TEST 60: Integer Body ✓",
            body=67890
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_61_html_injection_in_plain_text(self):
        """TEST 61: HTML in plain text mode should be escaped by client"""
        result = self.sender.sendEmail(
            subject="TEST 61: HTML in Plain Text ✓",
            body="<h1>This should appear as text</h1><script>alert('xss')</script>",
            html=False
        )
        self.assertTrue(result)
        time.sleep(0.5)

    def test_62_very_long_recipient_email(self):
        """TEST 62: Very long recipient email (should fail if too long)"""
        long_email = "a" * 200 + "@example.com"
        result = self.sender.sendEmail(
            subject="Should probably not send",
            body="Very long recipient email",
            recipient=long_email
        )
        # May or may not succeed depending on SMTP server limits
        # We just verify it doesn't crash
        self.assertIsInstance(result, bool)

    def test_63_concurrent_sends(self):
        """TEST 63: Concurrent email sends from multiple threads"""
        results = []
        
        def send_email(index):
            result = self.sender.sendEmail(
                subject=f"TEST 63: Concurrent Send {index}/10 ✓",
                body=f"Email from thread {index}"
            )
            results.append(result)
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=send_email, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # At least some should succeed
        self.assertGreater(sum(results), 0)
        time.sleep(1)

    def test_64_smtp_server_with_protocol(self):
        """TEST 64: SMTP server with protocol prefix (should still work)"""
        sender = EmailSender(
            smtp_server="smtp://" + SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )
        # This might fail, but shouldn't crash
        result = sender.sendEmail(
            subject="TEST 64: Protocol Prefix",
            body="SMTP server had protocol prefix"
        )
        self.assertIsInstance(result, bool)


class TestStressTests(unittest.TestCase):
    """Stress tests and performance tests"""

    def setUp(self):
        """Create valid sender for each test"""
        pythonEmailNotify.ENABLE_LOGGING = False
        self.sender = EmailSender(
            smtp_server=SMTP_SERVER,
            port=SMTP_PORT,
            login=EMAIL_ADDRESS,
            password=EMAIL_PASSWORD,
            default_recipient=MAIN_EMAIL_ADDRESS
        )

    def test_65_massive_body_1mb(self):
        """TEST 65: 1MB email body"""
        large_body = "TEST 65: Large body\n" + ("X" * (1024 * 1024))
        result = self.sender.sendEmail(
            subject="TEST 65: 1MB Body ✓",
            body=large_body
        )
        self.assertTrue(result)
        time.sleep(1)

    def test_66_many_sequential_sends(self):
        """TEST 66: 20 sequential email sends"""
        results = []
        for i in range(20):
            result = self.sender.sendEmail(
                subject=f"TEST 66: Sequential {i+1}/20 ✓",
                body=f"Sequential send #{i+1}"
            )
            results.append(result)
            time.sleep(0.2)  # Small delay for rate limiting
        
        # Most should succeed
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.8)

    def test_67_binary_like_content(self):
        """TEST 67: Binary-like content in body"""
        binary_content = "TEST 67: Binary content\n" + "\x00\x01\x02\x03\xff\xfe"
        result = self.sender.sendEmail(
            subject="TEST 67: Binary Content ✓",
            body=binary_content
        )
        # Should handle it somehow (convert, escape, or fail gracefully)
        self.assertIsInstance(result, bool)
        time.sleep(0.5)


def run_tests():
    """Run all tests with detailed output"""
    print("=" * 80)
    print("PRODUCTION-GRADE TEST SUITE FOR pythonEmailNotify.py")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  SMTP Server: {SMTP_SERVER}")
    print(f"  SMTP Port: {SMTP_PORT}")
    print(f"  From: {EMAIL_ADDRESS}")
    print(f"  To: {MAIN_EMAIL_ADDRESS}")
    print(f"\nNOTE: This will send many test emails to {MAIN_EMAIL_ADDRESS}")
    print("Each email has a unique subject indicating which test it's from.")
    print("=" * 80)
    print()
    
    # Run tests with verbose output
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())