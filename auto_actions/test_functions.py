#!/usr/bin/env python3
"""
Test script for auto action functions
Allows testing individual functions and actions
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to Python path so we can import funcs
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from funcs import AutoActionFunctions, checkstats
except ImportError as e:
    print(f"❌ Error importing functions: {e}")
    print("Make sure funcs.py exists in the same directory")
    sys.exit(1)


class FunctionTester:
    def __init__(self):
        self.functions = AutoActionFunctions()
        self.test_results = {}
    
    def log_test_result(self, test_name, success, details=""):
        """Log the result of a test"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results[test_name] = success
        
        print(f"[{timestamp}] {status} - {test_name}")
        if details:
            print(f"   📝 {details}")
        print()
    
    def test_screen_capture(self):
        """Test screen capture functionality"""
        print("🧪 Testing screen capture...")
        try:
            screen = self.functions.capture_screen()
            success = screen is not None
            details = f"Screen dimensions: {screen.shape if success else 'Failed to capture'}"
            self.log_test_result("Screen Capture", success, details)
            return success
        except Exception as e:
            self.log_test_result("Screen Capture", False, f"Exception: {e}")
            return False
    
    def test_template_loading(self):
        """Test template loading"""
        print("🧪 Testing template loading...")
        try:
            # Check if stats template was loaded
            stats_loaded = self.functions.stats_template is not None
            details = f"Stats template loaded: {stats_loaded}"
            
            # You can add more template checks here as you add more images
            self.log_test_result("Template Loading", stats_loaded, details)
            return stats_loaded
        except Exception as e:
            self.log_test_result("Template Loading", False, f"Exception: {e}")
            return False
    
    def test_key_press(self, key='tab'):
        """Test key press functionality"""
        print(f"🧪 Testing key press ({key})...")
        print("⚠️  This will actually press a key! Cancel within 3 seconds if needed...")
        
        for i in range(3, 0, -1):
            print(f"   Pressing {key} in {i} seconds...")
            time.sleep(1)
        
        try:
            success = self.functions.press_key(key, f"test {key} key")
            self.log_test_result(f"Key Press ({key})", success)
            return success
        except Exception as e:
            self.log_test_result(f"Key Press ({key})", False, f"Exception: {e}")
            return False
    
    def test_checkstats_function(self, skill='magic'):
        """Test the checkstats function"""
        print(f"🧪 Testing checkstats function with skill: {skill}")
        print("⚠️  This will open stats and move mouse! Cancel within 5 seconds if needed...")
        
        for i in range(5, 0, -1):
            print(f"   Starting checkstats test in {i} seconds...")
            time.sleep(1)
        
        try:
            success = self.functions.checkstats(skill)
            details = f"Tested with skill: {skill}"
            self.log_test_result(f"Checkstats Function ({skill})", success, details)
            return success
        except Exception as e:
            self.log_test_result(f"Checkstats Function ({skill})", False, f"Exception: {e}")
            return False
    
    def test_mouse_movement(self):
        """Test mouse movement functionality (without clicking)"""
        print("🧪 Testing mouse movement...")
        print("⚠️  This will move the mouse! Cancel within 3 seconds if needed...")
        
        for i in range(3, 0, -1):
            print(f"   Moving mouse in {i} seconds...")
            time.sleep(1)
        
        try:
            import pyautogui
            
            # Get current position
            start_x, start_y = pyautogui.position()
            print(f"   📍 Starting position: ({start_x}, {start_y})")
            
            # Move to a nearby position
            target_x = start_x + 50
            target_y = start_y + 50
            
            # Use the function's variation method
            varied_position = self.functions.add_click_variation((target_x, target_y))
            final_x, final_y = varied_position
            
            pyautogui.moveTo(final_x, final_y, duration=0.5)
            time.sleep(0.5)
            
            # Move back
            pyautogui.moveTo(start_x, start_y, duration=0.5)
            
            end_x, end_y = pyautogui.position()
            success = abs(end_x - start_x) < 10 and abs(end_y - start_y) < 10
            
            details = f"Moved to ({final_x}, {final_y}) and back to ({end_x}, {end_y})"
            self.log_test_result("Mouse Movement", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("Mouse Movement", False, f"Exception: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Running all function tests...")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            ("Screen Capture", self.test_screen_capture),
            ("Template Loading", self.test_template_loading),
            ("Mouse Movement", self.test_mouse_movement),
            ("Key Press", lambda: self.test_key_press('tab')),
        ]
        
        # Ask user if they want to test checkstats (more disruptive)
        print("\n📋 Basic tests completed. Do you want to test the checkstats function?")
        print("⚠️  This will open RuneScape stats and move the mouse to a skill.")
        user_input = input("Test checkstats? (y/n): ").lower().strip()
        
        if user_input in ['y', 'yes']:
            skill = input("Enter skill name (default: magic): ").strip() or 'magic'
            tests.append((f"Checkstats ({skill})", lambda: self.test_checkstats_function(skill)))
        
        # Run all tests
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            test_func()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for success in self.test_results.values() if success)
        total = len(self.test_results)
        
        for test_name, success in self.test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n📈 Results: {passed}/{total} tests passed")
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {total - passed} test(s) failed")


def main():
    """Main function to run tests"""
    print("🧪 Auto Actions Function Tester")
    print("=" * 60)
    print("This script tests individual functions from the funcs.py module.")
    print("Some tests will move the mouse and press keys - be ready to cancel if needed!")
    print()
    
    # Check if required packages are available
    try:
        import cv2
        import numpy as np
        import pyautogui
        print("✅ All required packages available")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Install with: pip install opencv-python numpy pyautogui")
        return
    
    print("\nChoose an option:")
    print("1. Run all tests")
    print("2. Test specific function")
    print("3. Test checkstats only")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    tester = FunctionTester()
    
    if choice == '1':
        tester.run_all_tests()
    
    elif choice == '2':
        print("\nAvailable tests:")
        print("1. Screen capture")
        print("2. Template loading")
        print("3. Mouse movement")
        print("4. Key press")
        print("5. Checkstats function")
        
        test_choice = input("Enter test number (1-5): ").strip()
        
        if test_choice == '1':
            tester.test_screen_capture()
        elif test_choice == '2':
            tester.test_template_loading()
        elif test_choice == '3':
            tester.test_mouse_movement()
        elif test_choice == '4':
            key = input("Enter key to test (default: tab): ").strip() or 'tab'
            tester.test_key_press(key)
        elif test_choice == '5':
            skill = input("Enter skill name (default: magic): ").strip() or 'magic'
            tester.test_checkstats_function(skill)
        else:
            print("❌ Invalid choice")
    
    elif choice == '3':
        skill = input("Enter skill name to test (default: magic): ").strip() or 'magic'
        tester.test_checkstats_function(skill)
    
    elif choice == '4':
        print("👋 Goodbye!")
        return
    
    else:
        print("❌ Invalid choice")
    
    # Print final summary if any tests were run
    if tester.test_results:
        tester.print_summary()


if __name__ == "__main__":
    main()
