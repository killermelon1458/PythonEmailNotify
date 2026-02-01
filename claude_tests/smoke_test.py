#!/usr/bin/env python3
"""
Quick Smoke Test for pythonEmailNotify.py

Run this first to verify your environment is set up correctly
before running the full test suite.
"""

import os
import sys

def check_environment():
    """Check that all required environment variables are set"""
    print("Checking environment variables...")
    
    required_vars = ["EMAIL_ADDRESS", "EMAIL_PASSWORD", "MAIN_EMAIL_ADDRESS"]
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask password for display
            display_value = "***" if "PASSWORD" in var else value
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  ✗ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\nERROR: Missing required environment variables: {', '.join(missing)}")
        print("\nPlease set them before running tests:")
        for var in missing:
            print(f"  export {var}='your_value'")
        return False
    
    print("\n✓ All environment variables are set!")
    return True


def check_module():
    """Check that pythonEmailNotify.py can be imported"""
    print("\nChecking pythonEmailNotify.py module...")
    
    try:
        import pythonEmailNotify
        print("  ✓ Module imported successfully")
        
        # Check key components
        if hasattr(pythonEmailNotify, 'EmailSender'):
            print("  ✓ EmailSender class found")
        else:
            print("  ✗ EmailSender class not found")
            return False
            
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import module: {e}")
        print("\nMake sure pythonEmailNotify.py is in the same directory as this script")
        return False


def run_smoke_test():
    """Run a quick smoke test to verify basic functionality"""
    print("\nRunning smoke test...")
    
    try:
        from pythonEmailNotify import EmailSender
        
        sender = EmailSender(
            smtp_server="smtp.gmail.com",
            port=587,
            login=os.getenv("EMAIL_ADDRESS"),
            password=os.getenv("EMAIL_PASSWORD"),
            default_recipient=os.getenv("MAIN_EMAIL_ADDRESS")
        )
        
        print("  ✓ EmailSender created successfully")
        
        # Send a test email
        print("  Sending smoke test email...")
        result = sender.sendEmail(
            subject="🔥 SMOKE TEST: pythonEmailNotify.py",
            body="If you receive this, the basic email sending is working!\n\nYou can now run the full test suite."
        )
        
        if result:
            print("  ✓ Smoke test email sent successfully!")
            print(f"\n  Check {os.getenv('MAIN_EMAIL_ADDRESS')} for the test email.")
            return True
        else:
            print("  ✗ Smoke test email failed to send")
            return False
            
    except Exception as e:
        print(f"  ✗ Smoke test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all pre-flight checks"""
    print("=" * 80)
    print("SMOKE TEST FOR pythonEmailNotify.py")
    print("=" * 80)
    print()
    
    checks = [
        ("Environment Variables", check_environment),
        ("Module Import", check_module),
        ("Basic Email Send", run_smoke_test)
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
            print(f"\n✗ {name} check FAILED\n")
            break
        print()
    
    print("=" * 80)
    if all_passed:
        print("✓ ALL SMOKE TESTS PASSED!")
        print("\nYou can now run the full test suite:")
        print("  python test_pythonEmailNotify.py")
    else:
        print("✗ SMOKE TESTS FAILED")
        print("\nPlease fix the issues above before running the full test suite.")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())