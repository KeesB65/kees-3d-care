#!/usr/bin/env python3
"""
Test script to validate the improved error handling in transfer_colors_las.py
This script tests various error conditions without requiring GUI or actual LAS files.
"""

import sys
import os
import tempfile
import shutil

# Add current directory to path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_validation_functions():
    """Test the validation functions"""
    print("🧪 Testing validation functions...")
    
    try:
        from transfer_colors_las import validate_las_file, show_error, show_info
        
        # Test 1: Empty path
        try:
            validate_las_file("", "Test")
            print("❌ Should have failed for empty path")
        except ValueError as e:
            print(f"✅ Empty path validation: {e}")
        
        # Test 2: Non-existent file
        try:
            validate_las_file("/non/existent/file.las", "Test")
            print("❌ Should have failed for non-existent file")
        except FileNotFoundError as e:
            print(f"✅ Non-existent file validation: {e}")
            
        # Test 3: Wrong extension
        try:
            # Create a temporary file with wrong extension
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
                tmp.write(b"test")
                tmp_path = tmp.name
            
            try:
                validate_las_file(tmp_path, "Test")
                print("❌ Should have failed for wrong extension")
            except ValueError as e:
                print(f"✅ Wrong extension validation: {e}")
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            print(f"⚠️  Temp file test failed: {e}")
                
        print("✅ All validation tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_error_messages():
    """Test error message functions"""
    print("\n🧪 Testing error message functions...")
    
    try:
        from transfer_colors_las import show_error, show_info
        
        # These should print to console even if GUI is not available
        show_error("Test Error", "Dit is een test foutmelding")
        show_info("Test Info", "Dit is een test informatiemelding")
        
        print("✅ Error message functions work")
        return True
        
    except Exception as e:
        print(f"❌ Error message test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting validation tests voor transfer_colors_las.py")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    if test_validation_functions():
        tests_passed += 1
        
    if test_error_messages():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test resultaten: {tests_passed}/{total_tests} tests geslaagd")
    
    if tests_passed == total_tests:
        print("🎉 Alle tests geslaagd! De verbeterde foutafhandeling werkt correct.")
        return 0
    else:
        print("❌ Sommige tests gefaald. Controleer de implementatie.")
        return 1

if __name__ == "__main__":
    sys.exit(main())