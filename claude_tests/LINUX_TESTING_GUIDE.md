# Linux Platform Testing Guide

## 🐧 Most Critical Tests for Linux

When running on Linux (especially servers), these are the tests most likely to expose platform-specific issues:

## 📋 Quick Test Suite (15 tests)

Run this first on Linux:
```bash
python linux_quick_test.py
```

### Why These 15 Tests Matter on Linux:

#### 1. **Network/SMTP Tests** (5 tests)
**Tests: 01, 25, 26, 34, 35**

**Why they might fail on Linux:**
- Different OpenSSL/TLS implementations
- Firewall rules blocking port 587
- SELinux or AppArmor restrictions
- Different DNS resolution behavior
- Corporate proxies or network policies

**What to check if they fail:**
```bash
# Check if port 587 is open
telnet smtp.gmail.com 587

# Check firewall
sudo iptables -L | grep 587
sudo ufw status

# Check SELinux (RHEL/CentOS)
getenforce
```

---

#### 2. **Threading Tests** (2 tests)
**Tests: 45, 63**

**Why they might fail on Linux:**
- Different threading implementation (pthread vs Windows threads)
- Different GIL behavior
- Resource limits (ulimit)
- Different scheduler behavior under load

**What to check if they fail:**
```bash
# Check thread limits
ulimit -u

# Check system limits
cat /proc/sys/kernel/threads-max

# Monitor during test
watch -n 1 'ps -eLf | grep python | wc -l'
```

---

#### 3. **Timeout Tests** (2 tests)
**Tests: 51, 54**

**Why they might fail on Linux:**
- Different socket timeout behavior
- systemd-resolved interfering with DNS
- Network namespaces in containers
- iptables DROP vs REJECT behavior

**What to check if they fail:**
```bash
# Test DNS resolution
dig smtp.gmail.com
nslookup smtp.gmail.com

# Check if running in container
cat /proc/1/cgroup | grep docker

# Test socket timeout behavior
timeout 15 telnet 10.255.255.1 587
```

---

#### 4. **File System/Logging Tests** (2 tests)
**Tests: 55, 56**

**Why they might fail on Linux:**
- Different file paths (`/` vs `\`)
- Permissions (root vs user)
- Read-only file systems
- tmpfs or ramdisk limitations
- NFS or network mounts

**What to check if they fail:**
```bash
# Check write permissions
ls -la $(pwd)

# Check filesystem type
df -T .

# Check disk space
df -h

# Check if directory is writable
touch test_write && rm test_write
```

---

#### 5. **Stress Tests** (2 tests)
**Tests: 65, 66**

**Why they might fail on Linux:**
- Memory limits (cgroups in containers)
- Rate limiting by systemd or firewall
- ulimit restrictions
- OOM killer intervention

**What to check if they fail:**
```bash
# Check memory limits
ulimit -m
ulimit -v

# Check if in container with limits
cat /sys/fs/cgroup/memory/memory.limit_in_bytes

# Monitor memory during test
watch -n 1 'free -h'

# Check OOM killer logs
dmesg | grep -i oom
```

---

#### 6. **Exception Handling Tests** (2 tests)
**Tests: 46, 47**

**Why they might fail on Linux:**
- Different stack trace format
- Different line endings in tracebacks
- Path separators in stack traces

**These should pass but verify the email content looks correct**

---

## 🚨 Known Linux-Specific Issues

### Issue 1: Port 587 Blocked
**Symptoms:** Test 25, 26 fail with connection timeout
**Solution:**
```bash
# Allow outbound SMTP
sudo ufw allow out 587/tcp
# Or for iptables
sudo iptables -A OUTPUT -p tcp --dport 587 -j ACCEPT
```

### Issue 2: SELinux Denying Network Access
**Symptoms:** "Permission denied" on SMTP connection
**Solution:**
```bash
# Check SELinux denials
sudo ausearch -m avc -ts recent

# Temporarily disable (NOT for production!)
sudo setenforce 0

# Or create proper policy (production way)
sudo setsebool -P httpd_can_network_connect 1
```

### Issue 3: Low ulimit on Threads
**Symptoms:** Test 63 fails with "can't start new thread"
**Solution:**
```bash
# Increase limit temporarily
ulimit -u 4096

# Permanently (edit /etc/security/limits.conf)
echo "* soft nproc 4096" | sudo tee -a /etc/security/limits.conf
```

### Issue 4: Docker/Container Environment
**Symptoms:** Various networking issues
**Solution:**
```bash
# Run with host network
docker run --network=host ...

# Or add explicit DNS
docker run --dns 8.8.8.8 ...
```

---

## 🎯 Minimal Sanity Check (3 tests, 1 minute)

If you just want to verify basic functionality on Linux:

```bash
python -c "
import unittest
from test_pythonEmailNotify import TestConfigurationValidation, TestEmailSending

suite = unittest.TestSuite()
suite.addTest(TestConfigurationValidation('test_01_valid_configuration'))
suite.addTest(TestEmailSending('test_25_send_plain_text_email'))
suite.addTest(TestEmailSending('test_45_rapid_succession_sends'))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
exit(0 if result.wasSuccessful() else 1)
"
```

---

## 📊 Full Suite on Linux

If you want to run everything (just like on Windows):

```bash
# All 67 tests (~50 emails, ~3 minutes)
python test_pythonEmailNotify.py
```

**Expected differences on Linux:**
- Tests should complete ~10-20% faster (better threading)
- File I/O may be faster (better disk scheduler)
- Network tests may take longer (if behind corporate firewall)

---

## 🔍 Debugging Failed Tests on Linux

### Enable verbose output:
```bash
python -u linux_quick_test.py 2>&1 | tee test_output.log
```

### Check system logs:
```bash
# Check syslog for issues
sudo tail -f /var/log/syslog

# Check for Python errors
journalctl -f | grep python
```

### Network debugging:
```bash
# Capture SMTP traffic
sudo tcpdump -i any port 587 -w smtp.pcap

# Monitor in real-time
sudo tcpdump -i any port 587 -A
```

### Strace for system calls:
```bash
# See what's happening at syscall level
strace -e trace=network python linux_quick_test.py
```

---

## ✅ Expected Results on Linux

**On a well-configured Linux system:**
- All 15 Linux-specific tests should pass
- Tests 54 (timeout) might take the full 10+ seconds
- Tests 63 (concurrent) might be slightly faster than Windows
- Logging tests should create files in `/tmp` or current directory

**On a restrictive Linux system (container, SELinux, etc.):**
- Network tests (51, 54) might fail → Check firewall/SELinux
- Threading test (63) might fail → Check ulimit
- Logging tests (55, 56) might fail → Check permissions

---

## 🐳 Docker-Specific Testing

If running in Docker:

```dockerfile
FROM python:3.11-slim

# Install test dependencies
RUN pip install --no-cache-dir pythonEmailNotify

# Copy tests
COPY test_pythonEmailNotify.py linux_quick_test.py pythonEmailNotify.py ./

# Run tests
CMD ["python", "linux_quick_test.py"]
```

Run with:
```bash
docker build -t email-test .
docker run --rm \
  -e EMAIL_ADDRESS="your@email.com" \
  -e EMAIL_PASSWORD="your-app-password" \
  -e MAIN_EMAIL_ADDRESS="recipient@email.com" \
  email-test
```

---

## 📝 Summary

**Use `linux_quick_test.py` when:**
- First time deploying to Linux
- Moving between Linux distributions
- Testing in containers/VMs
- Setting up CI/CD pipelines
- Diagnosing platform-specific issues

**The 15 tests cover:**
- ✅ SMTP/SSL/TLS compatibility
- ✅ Threading behavior
- ✅ Network timeouts
- ✅ File system operations
- ✅ Resource limits
- ✅ Exception handling

**If all 15 pass → Your code is Linux-ready! 🐧**
