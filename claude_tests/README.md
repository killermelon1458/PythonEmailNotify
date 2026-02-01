# Production-Grade Test Suite for pythonEmailNotify.py

This comprehensive test suite is designed to rigorously test every aspect of the `pythonEmailNotify.py` email notification system, including edge cases, error conditions, and stress scenarios.

## 📋 Test Coverage

The test suite includes **67 tests** across the following categories:

### Configuration Validation (Tests 1-24)
- Valid configuration
- Missing/empty/invalid SMTP server, port, login, password
- Whitespace-only values
- Type validation (non-strings, non-numbers)
- Port range validation (1-65535)
- Invalid email formats
- Multiple simultaneous validation errors
- Strict vs. lenient validation modes

### Email Sending (Tests 25-45)
- Plain text and HTML emails
- Default vs. override recipients
- Empty/None subjects and bodies
- Unicode characters (Chinese, Arabic, Russian, emoji)
- Very long subjects and bodies
- Special characters and newlines
- HTML with script tags
- Invalid recipient formats
- Rapid succession sends (rate limiting)

### Exception Handling (Tests 46-50)
- Simple exceptions
- Exceptions with full tracebacks
- None as exception (edge case)
- Unicode in exception messages
- Override recipient for exception reports

### Network Failures (Tests 51-54)
- Invalid SMTP server
- Invalid port
- Wrong credentials
- Timeout handling

### Logging System (Tests 55-56)
- Logging enabled/disabled
- Log file creation
- Non-blocking queue-based logging

### Edge Cases (Tests 57-64)
- Recipient whitespace trimming
- Port as string conversion
- Integer subject/body conversion
- HTML injection in plain text
- Very long recipient emails
- Concurrent sends from multiple threads
- SMTP server with protocol prefix

### Stress Tests (Tests 65-67)
- 1MB email body
- 20 sequential sends
- Binary-like content

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Make sure pythonEmailNotify.py is in the same directory
ls -la pythonEmailNotify.py

# Set your environment variables
export EMAIL_ADDRESS="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export MAIN_EMAIL_ADDRESS="recipient@example.com"
```

**Important**: For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

### 2. Run Smoke Test First

```bash
# Quick check that everything is configured correctly
python smoke_test.py
```

This will:
- Verify environment variables are set
- Test module import
- Send a single smoke test email

### 3. Run Full Test Suite

```bash
# Run all 67 tests (will send many emails!)
python test_pythonEmailNotify.py
```

## 📧 What to Expect

The test suite will send **many emails** to `MAIN_EMAIL_ADDRESS`. Each email has a unique subject line that indicates which test it's from:

- `TEST 01: Valid Configuration ✓`
- `TEST 25: Plain Text Email ✓`
- `TEST 34: Unicode ✓ 你好 🎉 العربية`
- `TEST 45: Rapid Send 1/5 ✓`
- etc.

**Successful tests** will have a ✓ in the subject line.
**Failed tests** won't send an email (or will send with diagnostic info).

## 📊 Test Output

The test suite provides detailed output:

```
====================================================================================
PRODUCTION-GRADE TEST SUITE FOR pythonEmailNotify.py
====================================================================================

Configuration:
  SMTP Server: smtp.gmail.com
  SMTP Port: 587
  From: your-email@gmail.com
  To: recipient@example.com

NOTE: This will send many test emails to recipient@example.com
Each email has a unique subject indicating which test it's from.
====================================================================================

test_01_valid_configuration (__main__.TestConfigurationValidation) ... ok
test_02_missing_smtp_server (__main__.TestConfigurationValidation) ... ok
test_03_empty_smtp_server (__main__.TestConfigurationValidation) ... ok
...

====================================================================================
TEST SUMMARY
====================================================================================
Tests run: 67
Successes: 65
Failures: 2
Errors: 0
====================================================================================
```

## 🔍 Test Categories Explained

### Configuration Validation Tests
These verify that the EmailSender properly validates all input parameters and fails gracefully with clear diagnostics when configuration is invalid.

### Email Sending Tests
These verify that emails are sent successfully under various conditions, including edge cases like empty subjects, Unicode characters, very long content, etc.

### Network Failure Tests
These verify that the system handles network issues gracefully without crashing, including timeouts, wrong credentials, and unreachable servers.

### Stress Tests
These verify that the system can handle large payloads and high volumes without degrading or failing.

## 🛠️ Customization

You can customize the test suite by editing these variables at the top of `test_pythonEmailNotify.py`:

```python
SMTP_SERVER = "smtp.gmail.com"  # Change for other providers
SMTP_PORT = 587                 # Change if needed
```

## ⚠️ Known Behaviors

1. **Rate Limiting**: Gmail and other providers may rate-limit your sends. The test suite includes small delays between emails, but you may still hit limits with rapid tests.

2. **Test 53 (Wrong Credentials)**: This test intentionally uses wrong credentials and expects failure. You'll see authentication errors in the output - this is expected.

3. **Test 51 (Invalid SMTP Server)**: This test uses a fake SMTP server and expects timeout/connection failure.

4. **Concurrent Tests**: Tests 63 and 64 send emails from multiple threads simultaneously. Some may fail due to SMTP connection limits.

## 🐛 Troubleshooting

### "Environment variables not set"
Make sure you've exported all three required variables:
```bash
export EMAIL_ADDRESS="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export MAIN_EMAIL_ADDRESS="recipient@example.com"
```

### "535 Authentication failed"
You're likely using your regular Gmail password instead of an App Password. Create an App Password at: https://myaccount.google.com/apppasswords

### "Connection timeout"
Check your network connection and firewall settings. Port 587 must be open for outbound SMTP.

### "Too many emails sent"
Gmail has sending limits. Wait a few hours and try again, or reduce the number of tests.

## 📝 Test Design Philosophy

This test suite follows these principles:

1. **Every email tells a story**: Each test email has a descriptive subject indicating what it's testing
2. **Fail loudly**: Tests that expect failure verify the failure happens gracefully
3. **No silent failures**: All operations return status booleans that are checked
4. **Stress the boundaries**: Test edge cases, invalid inputs, and extreme values
5. **Real network tests**: Most tests use real SMTP to catch real-world issues

## 🎯 Expected Results

With proper configuration:
- **Configuration tests**: 24 tests, ~20 should pass (some intentionally test failures)
- **Email sending tests**: 21 tests, ~20 should pass
- **Exception tests**: 5 tests, all should pass
- **Network tests**: 4 tests, ~1-2 should pass (others intentionally fail)
- **Logging tests**: 2 tests, all should pass
- **Edge case tests**: 8 tests, ~6 should pass
- **Stress tests**: 3 tests, ~2 should pass (depending on rate limits)

**Total**: ~55-60 tests passing out of 67 is expected and good!

## 📧 Email Summary

After running the full suite, you should receive approximately:
- **40-50 successful test emails** with descriptive subjects
- **0 emails** from failed tests (they won't send)

Check your inbox to verify the emails arrived and have meaningful subjects.

## 🤝 Contributing

To add new tests:

1. Add a new test method to the appropriate TestCase class
2. Follow the naming convention: `test_XX_descriptive_name`
3. Include the test number in the email subject: `TEST XX: Description ✓`
4. Add a docstring explaining what's being tested
5. Use `time.sleep(0.5)` after sends to avoid rate limiting

## 📄 License

This test suite is provided as-is for testing the pythonEmailNotify.py module.

---

**Happy Testing!** 🚀