#!/usr/bin/env python3
"""
Skills Tab Toggle Test
Test clicking skills tab vs pressing '4' key to toggle skills interface
"""

import sys
import os
import time
import random
from datetime import datetime

# Add the parent directory to Python path so we can import funcs
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

try:
    from funcs import AutoActionFunctions
    import pyautogui
    import cv2
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Make sure funcs.py exists and required packages are installed")
    sys.exit(1)


class SkillsTabTester:
    def __init__(self):
        self.functions = AutoActionFunctions()
        self.skills_tab_template = None
        self.load_skills_tab_template()
    
    def load_skills_tab_template(self):
        """Load the skills tab template"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            skills_tab_path = os.path.join(current_dir, "images", "skills_tab.png")
            
            if os.path.exists(skills_tab_path):
                self.skills_tab_template = cv2.imread(skills_tab_path)
                print(f"✅ Loaded skills tab template from {skills_tab_path}")
                return True
            else:
                print(f"❌ Skills tab template not found at {skills_tab_path}")
                print("💡 Please create skills_tab.png in images/ directory")
                return False
        except Exception as e:
            print(f"❌ Error loading skills tab template: {e}")
            return False
    
    def find_skills_tab(self, screen):
        """Find the skills tab on screen"""
        if self.skills_tab_template is None:
            print("❌ No skills tab template loaded")
            return None, 0
        
        position, confidence = self.functions.find_template(screen, self.skills_tab_template, threshold=0.6)
        return position, confidence
    
    def is_skills_interface_open(self, screen):
        """Check if skills interface is currently open by detecting any skill"""
        # Check for a few reliable skills to see if stats page is open
        test_skills = ['attack', 'magic', 'mining', 'hitpoints']
        
        for skill in test_skills:
            if skill in self.functions.skill_templates:
                skill_position = self.functions.find_skill_position(screen, skill)
                if skill_position:
                    return True, f"Found {skill} skill - stats page is open"
        
        return False, "No skills detected - stats page is closed"
    
    def wait_for_pause_unpause(self, action_description):
        """Wait for user to press 'p' to start action"""
        print(f"⏸️  PAUSED - {action_description}")
        print("   Click into your game screen and press 'p' to start")
        
        from pynput import keyboard
        is_paused = True
        
        def on_key_press(key):
            nonlocal is_paused
            try:
                if key.char == 'p':
                    is_paused = False
                    print("▶️  UNPAUSED - Starting action...")
                    return False  # Stop listener
            except AttributeError:
                pass
        
        listener = keyboard.Listener(on_press=on_key_press)
        listener.start()
        
        while is_paused:
            time.sleep(0.1)
        
        listener.stop()
    
    def test_press_4_key(self):
        """Test full toggle cycle with '4' key"""
        print("\n🧪 Test 1: Press '4' Key Full Cycle")
        print("-" * 40)
        
        self.wait_for_pause_unpause("Ready to test full '4' key toggle cycle")
        
        # Step 1: Press '4' to open stats
        print("⌨️ Step 1: Pressing '4' to open stats...")
        success1 = self.functions.press_key('4', "open stats")
        if not success1:
            return False, "Failed to press '4' key (open)"
        
        time.sleep(0.5)  # Wait for interface to load
        
        # Step 2: Check if stats are visible
        screen1 = self.functions.capture_screen()
        if screen1 is None:
            return False, "Could not capture screen after opening"
        
        stats_open, details1 = self.is_skills_interface_open(screen1)
        print(f"📊 After opening: {details1}")
        
        if not stats_open:
            return False, "Stats page did not open after pressing '4'"
        
        # Step 3: Press '4' again to close stats
        print("⌨️ Step 2: Pressing '4' again to close stats...")
        success2 = self.functions.press_key('4', "close stats")
        if not success2:
            return False, "Failed to press '4' key (close)"
        
        time.sleep(0.5)  # Wait for interface to close
        
        # Step 4: Check if stats are hidden
        screen2 = self.functions.capture_screen()
        if screen2 is None:
            return False, "Could not capture screen after closing"
        
        stats_closed, details2 = self.is_skills_interface_open(screen2)
        print(f"📊 After closing: {details2}")
        
        if stats_closed:
            return False, "Stats page did not close after pressing '4' again"
        
        print("✅ SUCCESS: '4' key toggle cycle completed!")
        print("   ✅ '4' opened stats page")
        print("   ✅ '4' closed stats page")
        return True, "Full '4' key cycle successful"
    
    def test_click_skills_tab(self):
        """Test full toggle cycle by clicking skills tab"""
        print("\n🧪 Test 2: Click Skills Tab Full Cycle")
        print("-" * 40)
        
        if self.skills_tab_template is None:
            return False, "No skills tab template loaded"
        
        self.wait_for_pause_unpause("Ready to test full skills tab click cycle")
        
        # Step 1: Click skills tab to open stats
        screen1 = self.functions.capture_screen()
        if screen1 is None:
            return False, "Could not capture initial screen"
        
        tab_position1, tab_confidence1 = self.find_skills_tab(screen1)
        if not tab_position1 or tab_confidence1 < 0.6:
            return False, f"Could not find skills tab (confidence: {tab_confidence1:.2f})"
        
        print(f"🎯 Found skills tab at {tab_position1} (confidence: {tab_confidence1:.2f})")
        
        # Click to open
        template_height, template_width = self.skills_tab_template.shape[:2]
        center_x, center_y = tab_position1
        half_width = template_width // 2
        half_height = template_height // 2
        
        random_x = random.randint(center_x - half_width + 5, center_x + half_width - 5)
        random_y = random.randint(center_y - half_height + 5, center_y + half_height - 5)
        random_position1 = (random_x, random_y)
        
        print(f"🖱️ Step 1: Clicking skills tab to open stats...")
        print(f"   Position: {random_position1} (offset: {random_x - center_x:+d}, {random_y - center_y:+d})")
        
        success1 = self.functions.human_click(random_position1, "🎯 Click to open stats")
        if not success1:
            return False, "Failed to click skills tab (open)"
        
        time.sleep(0.5)  # Wait for interface to load
        
        # Step 2: Check if stats are visible
        screen2 = self.functions.capture_screen()
        if screen2 is None:
            return False, "Could not capture screen after opening"
        
        stats_open, details1 = self.is_skills_interface_open(screen2)
        print(f"📊 After opening: {details1}")
        
        if not stats_open:
            return False, "Stats page did not open after clicking tab"
        
        # Step 3: Click skills tab again to close stats
        tab_position2, tab_confidence2 = self.find_skills_tab(screen2)
        if not tab_position2 or tab_confidence2 < 0.6:
            return False, f"Could not find skills tab for closing (confidence: {tab_confidence2:.2f})"
        
        # Click to close (with new randomization)
        center_x2, center_y2 = tab_position2
        random_x2 = random.randint(center_x2 - half_width + 5, center_x2 + half_width - 5)
        random_y2 = random.randint(center_y2 - half_height + 5, center_y2 + half_height - 5)
        random_position2 = (random_x2, random_y2)
        
        print(f"🖱️ Step 2: Clicking skills tab again to close stats...")
        print(f"   Position: {random_position2} (offset: {random_x2 - center_x2:+d}, {random_y2 - center_y2:+d})")
        
        success2 = self.functions.human_click(random_position2, "🎯 Click to close stats")
        if not success2:
            return False, "Failed to click skills tab (close)"
        
        time.sleep(0.5)  # Wait for interface to close
        
        # Step 4: Check if stats are hidden
        screen3 = self.functions.capture_screen()
        if screen3 is None:
            return False, "Could not capture screen after closing"
        
        stats_closed, details2 = self.is_skills_interface_open(screen3)
        print(f"📊 After closing: {details2}")
        
        if stats_closed:
            return False, "Stats page did not close after clicking tab again"
        
        print("✅ SUCCESS: Skills tab toggle cycle completed!")
        print("   ✅ Tab click opened stats page")
        print("   ✅ Tab click closed stats page")
        return True, "Full tab click cycle successful"
    
    def test_both_methods(self):
        """Test both methods and compare results"""
        print("🔄 Comprehensive Skills Tab Toggle Test")
        print("=" * 50)
        
        results = {}
        
        # Test pressing '4'
        success_4, message_4 = self.test_press_4_key()
        results['press_4'] = {'success': success_4, 'message': message_4}
        
        print("\n" + "="*30)
        input("Press Enter to continue to next test...")
        
        # Test clicking tab
        success_tab, message_tab = self.test_click_skills_tab()
        results['click_tab'] = {'success': success_tab, 'message': message_tab}
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SKILLS TAB TOGGLE TEST SUMMARY")
        print("=" * 60)
        
        print(f"\n⌨️ Press '4' Key:")
        status_4 = "✅ SUCCESS" if success_4 else "❌ FAILED"
        print(f"   {status_4} - {message_4}")
        
        print(f"\n🖱️ Click Skills Tab:")
        status_tab = "✅ SUCCESS" if success_tab else "❌ FAILED"
        print(f"   {status_tab} - {message_tab}")
        
        if success_4 and success_tab:
            print(f"\n🎉 EXCELLENT: Both methods work perfectly!")
            print("   ✅ Press '4' key toggles skills interface")
            print("   ✅ Click skills tab toggles skills interface")
        elif success_4 or success_tab:
            working = "Press '4'" if success_4 else "Click skills tab"
            broken = "Click skills tab" if success_4 else "Press '4'"
            print(f"\n⚠️ PARTIAL: {working} works, but {broken} needs fixing")
        else:
            print(f"\n❌ BOTH METHODS FAILED: Check templates and interface detection")
        
        return results


def main():
    """Main function"""
    print("🧪 Skills Tab Toggle Tester")
    print("=" * 50)
    print("Compare pressing '4' key vs clicking skills tab")
    print()
    
    # Check dependencies
    try:
        import cv2
        import numpy as np
        import pyautogui
        from pynput import keyboard
        print("✅ All required packages available")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        return
    
    tester = SkillsTabTester()
    
    if tester.skills_tab_template is None:
        print("\n❌ Cannot run tests without skills tab template")
        print("💡 Please create skills_tab.png in images/ directory")
        print("   - Take a screenshot of just the skills tab button")
        print("   - Save as images/skills_tab.png")
        return
    
    print("\nChoose test mode:")
    print("1. Test pressing '4' key only")
    print("2. Test clicking skills tab only") 
    print("3. Test both methods (comprehensive)")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        success, message = tester.test_press_4_key()
        print(f"\n📊 Result: {'✅ SUCCESS' if success else '❌ FAILED'} - {message}")
    
    elif choice == '2':
        success, message = tester.test_click_skills_tab()
        print(f"\n📊 Result: {'✅ SUCCESS' if success else '❌ FAILED'} - {message}")
    
    elif choice == '3':
        results = tester.test_both_methods()
    
    elif choice == '4':
        print("👋 Goodbye!")
        return
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
