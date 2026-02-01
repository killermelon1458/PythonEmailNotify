# Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Set Environment Variables
```bash
export EMAIL_ADDRESS="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"      # Use App Password for Gmail!
export MAIN_EMAIL_ADDRESS="recipient@example.com"
```

### Step 2: Run Smoke Test
```bash
python smoke_test.py
```
This sends 1 email to verify everything works.

### Step 3: Choose Your Testing Approach

**Option A - Interactive Menu (Recommended)**
```bash
python run_tests.py
```
Choose which tests to run from a menu.

**Option B - Full Suite**
```bash
python test_pythonEmailNotify.py
```
Runs all 67 tests (~50 emails sent).

---

## 📊 Test Categories

| Category | Tests | Emails | Command |
|----------|-------|--------|---------|
| Smoke Test | 1 | 1 | `python smoke_test.py` |
| Configuration | 24 | 0 | Via menu option 2 |
| Email Sending | 21 | 21 | Via menu option 4 |
| Exceptions | 5 | 5 | Via menu option 5 |
| Network Failures | 4 | 0 | Via menu option 6 |
| Edge Cases | 8 | 8 | Via menu option 7 |
| Stress Tests | 3 | 3 | Via menu option 8 |
| **Full Suite** | **67** | **~50** | Via menu option 9 |

---

## ✅ What Each Test Does

### Configuration Tests (Tests 1-24)
- Test 01: ✅ Valid config should work
- Tests 02-24: ❌ Invalid configs should fail gracefully

### Email Sending (Tests 25-45)
- Test 25: Plain text email
- Test 26: HTML email
- Test 34: Unicode (你好 🎉 العربية)
- Test 37: Very long body (10KB)
- Test 45: Rapid succession (5 emails)

### Exceptions (Tests 46-50)
- Test 46: Send simple exception
- Test 47: Exception with full traceback
- Test 49: Unicode in exception message

### Network Failures (Tests 51-54)
- Test 51: Invalid SMTP server (should fail)
- Test 53: Wrong password (should fail)
- Test 54: Timeout handling

### Edge Cases (Tests 57-64)
- Test 58: Port as string "587"
- Test 59: Integer subject
- Test 63: Concurrent sends (10 threads)

### Stress Tests (Tests 65-67)
- Test 65: 1MB email body
- Test 66: 20 sequential sends
- Test 67: Binary-like content

---

## 🔧 Gmail App Password Setup

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Click "Generate"
4. Copy the 16-character password
5. Use this as your `EMAIL_PASSWORD`

---

## 📧 What to Expect in Your Inbox

Each test email has a unique subject:
- ✅ `TEST 25: Plain Text Email ✓` - Successful test
- ✅ `TEST 34: Unicode ✓ 你好 🎉 العربية` - Unicode test
- ✅ `TEST 45: Rapid Send 1/5 ✓` - Part of sequence

Failed tests won't send emails.

---

## 🐛 Common Issues

**"Authentication failed"**
→ Use App Password, not regular password

**"Connection timeout"**
→ Check firewall, port 587 must be open

**"Too many emails"**
→ Gmail rate limit hit, wait a few hours

**"Module not found"**
→ Make sure `pythonEmailNotify.py` is in same directory

---

## 💡 Pro Tips

1. **Start small**: Run smoke test first
2. **Use the menu**: `run_tests.py` is easier than running all tests
3. **Watch your inbox**: Each test tells you what it's testing
4. **Rate limiting**: Some tests may fail due to Gmail limits (this is normal)
5. **Read the README**: Full documentation in `README.md`

---

## 📝 Files Included

- `test_pythonEmailNotify.py` - Full test suite (67 tests)
- `smoke_test.py` - Quick verification (1 test)
- `run_tests.py` - Interactive menu runner
- `README.md` - Comprehensive documentation
- `QUICKSTART.md` - This file

---

**Ready to test?** Start with: `python smoke_test.py`