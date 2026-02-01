#!/usr/bin/env python3
"""
Interactive Test Runner for pythonEmailNotify.py

Provides options to run different subsets of tests.
"""

import sys
import os
import unittest


def print_menu():
    """Display the test menu"""
    print("\n" + "=" * 80)
    print("PYTHONEMAILTIFY TEST RUNNER")
    print("=" * 80)
    print("\nSelect which tests to run:\n")
    print("  1. Smoke Test Only (1 email)")
    print("  2. Configuration Tests (0 emails - validation only)")
    print("  3. Basic Email Tests (10 emails)")
    print("  4. All Email Tests (21 emails)")
    print("  5. Exception Tests (5 emails)")
    print("  6. Network Failure Tests (0 emails - all should fail)")
    print("  7. Edge Case Tests (8 emails)")
    print("  8. Stress Tests (3 emails - large payloads)")
    print("  9. Full Suite (ALL 67 tests, ~50 emails)")
    print("  0. Exit")
    print("\n" + "=" * 80)


def run_smoke_test():
    """Run just the smoke test"""
    print("\nRunning smoke test...\n")
    os.system("python smoke_test.py")


def run_test_class(class_name):
    """Run tests from a specific class"""
    import test_pythonEmailNotify
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(f"test_pythonEmailNotify.{class_name}")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print_summary(result)
    return result.wasSuccessful()


def run_specific_tests(test_names):
    """Run specific test methods"""
    import test_pythonEmailNotify
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_name in test_names:
        suite.addTest(loader.loadTestsFromName(f"test_pythonEmailNotify.{test_name}"))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print_summary(result)
    return result.wasSuccessful()


def run_full_suite():
    """Run all tests"""
    print("\nRunning FULL test suite...\n")
    os.system("python test_pythonEmailNotify.py")


def print_summary(result):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)


def verify_environment():
    """Check if environment is set up"""
    required_vars = ["EMAIL_ADDRESS", "EMAIL_PASSWORD", "MAIN_EMAIL_ADDRESS"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("\n⚠️  WARNING: Missing environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set them before running tests:")
        for var in missing:
            print(f"  export {var}='your_value'")
        print()
        return False
    return True


def main():
    """Main interactive menu"""
    if not verify_environment():
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return 1
    
    while True:
        print_menu()
        choice = input("Enter your choice (0-9): ").strip()
        
        if choice == '0':
            print("\nExiting. Happy testing!\n")
            return 0
        
        elif choice == '1':
            run_smoke_test()
        
        elif choice == '2':
            print("\nRunning Configuration Validation Tests...")
            print("NOTE: These tests validate config without sending emails\n")
            run_test_class("TestConfigurationValidation")
        
        elif choice == '3':
            print("\nRunning Basic Email Tests (first 10)...")
            tests = [
                f"TestEmailSending.test_{i:02d}_{name}" 
                for i, name in [
                    (25, "send_plain_text_email"),
                    (26, "send_html_email"),
                    (27, "use_default_recipient"),
                    (28, "override_default_recipient"),
                    (30, "empty_subject"),
                    (32, "empty_body"),
                    (34, "unicode_subject"),
                    (35, "unicode_body"),
                    (38, "special_characters_subject"),
                    (40, "multiline_body")
                ]
            ]
            run_specific_tests(tests)
        
        elif choice == '4':
            print("\nRunning ALL Email Sending Tests...")
            print("NOTE: This will send 21 test emails\n")
            run_test_class("TestEmailSending")
        
        elif choice == '5':
            print("\nRunning Exception Handling Tests...")
            print("NOTE: This will send 5 test emails\n")
            run_test_class("TestExceptionHandling")
        
        elif choice == '6':
            print("\nRunning Network Failure Tests...")
            print("NOTE: These tests intentionally fail (no emails sent)\n")
            run_test_class("TestNetworkFailures")
        
        elif choice == '7':
            print("\nRunning Edge Case Tests...")
            print("NOTE: This will send ~8 test emails\n")
            run_test_class("TestEdgeCases")
        
        elif choice == '8':
            print("\nRunning Stress Tests...")
            print("NOTE: This will send 3 large emails\n")
            run_test_class("TestStressTests")
        
        elif choice == '9':
            confirm = input("\n⚠️  This will send ~50 emails! Continue? (y/N): ")
            if confirm.lower() == 'y':
                run_full_suite()
            else:
                print("Cancelled.")
        
        else:
            print("\n❌ Invalid choice. Please enter 0-9.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    sys.exit(main())