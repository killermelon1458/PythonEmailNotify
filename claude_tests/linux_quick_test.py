#!/usr/bin/env python3
"""
Linux-Specific Quick Test Suite for pythonEmailNotify.py

This runs only the tests most likely to behave differently on Linux:
- File system operations (logging, permissions)
- Threading behavior
- Network/SMTP (different SSL/TLS implementations)
- Timeout behavior
- Concurrent operations

Total: 15 critical tests (~10 emails sent)
Run time: ~30-40 seconds
"""

import os
import sys
import unittest

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


def run_linux_tests():
    """Run only tests that might behave differently on Linux"""
    
    print("=" * 80)
    print("LINUX-SPECIFIC TEST SUITE FOR pythonEmailNotify.py")
    print("=" * 80)
    print(f"\nTesting on: {sys.platform}")
    print(f"Python version: {sys.version}")
    print(f"\nConfiguration:")
    print(f"  SMTP Server: {SMTP_SERVER}")
    print(f"  SMTP Port: {SMTP_PORT}")
    print(f"  From: {EMAIL_ADDRESS}")
    print(f"  To: {MAIN_EMAIL_ADDRESS}")
    print("\n" + "=" * 80)
    print("\nRunning 15 platform-sensitive tests...")
    print("=" * 80)
    print()
    
    # Import test classes
    from test_pythonEmailNotify import (
        TestConfigurationValidation,
        TestEmailSending,
        TestNetworkFailures,
        TestLoggingSystem,
        TestEdgeCases,
        TestStressTests
    )
    
    # Create test suite with specific tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 1. Basic functionality (sanity check)
    suite.addTest(TestConfigurationValidation('test_01_valid_configuration'))
    
    # 2. Network/SMTP tests (SSL/TLS implementation may differ)
    suite.addTest(TestEmailSending('test_25_send_plain_text_email'))
    suite.addTest(TestEmailSending('test_26_send_html_email'))
    suite.addTest(TestEmailSending('test_34_unicode_subject'))
    suite.addTest(TestEmailSending('test_35_unicode_body'))
    
    # 3. Threading tests (Linux threading may differ from Windows)
    suite.addTest(TestEmailSending('test_45_rapid_succession_sends'))
    suite.addTest(TestEdgeCases('test_63_concurrent_sends'))
    
    # 4. Network failure/timeout tests (critical for Linux servers)
    suite.addTest(TestNetworkFailures('test_51_invalid_smtp_server'))
    suite.addTest(TestNetworkFailures('test_54_timeout_handling'))
    
    # 5. File system tests (permissions, paths differ on Linux)
    suite.addTest(TestLoggingSystem('test_55_logging_enabled'))
    suite.addTest(TestLoggingSystem('test_56_logging_disabled'))
    
    # 6. Stress tests (resource limits may differ)
    suite.addTest(TestStressTests('test_65_massive_body_1mb'))
    suite.addTest(TestStressTests('test_66_many_sequential_sends'))
    
    # 7. Exception handling (stack traces may look different)
    from test_pythonEmailNotify import TestExceptionHandling
    suite.addTest(TestExceptionHandling('test_46_send_simple_exception'))
    suite.addTest(TestExceptionHandling('test_47_send_exception_with_traceback'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 80)
    print("LINUX TEST SUMMARY")
    print("=" * 80)
    print(f"Platform: {sys.platform}")
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL LINUX-SPECIFIC TESTS PASSED!")
        print("Your code is compatible with Linux systems.")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Check the output above for platform-specific issues.")
    
    print("=" * 80)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_linux_tests())
