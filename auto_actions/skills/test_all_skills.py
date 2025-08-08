#!/usr/bin/env python3
"""
Test All Skills - Goes through each skill one by one
Tests all 23 RuneScape skills with random hover positioning
"""

import sys
import os
import time
from datetime import datetime

# Add the parent directory to Python path so we can import funcs
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

try:
    from funcs import AutoActionFunctions
except ImportError as e:
    print(f"❌ Error importing functions: {e}")
    print("Make sure funcs.py exists in the same directory")
    sys.exit(1)


class AllSkillsTester:
    def __init__(self):
        self.functions = AutoActionFunctions()
        self.test_results = {}
        
        # All 23 RuneScape skills in a logical order
        self.all_skills = [
            # Combat skills
            'attack', 'strength', 'defence', 'hitpoints', 'prayer', 'ranged', 'magic',
            # Gathering skills  
            'mining', 'fishing', 'woodcutting', 'farming', 'hunter',
            # Artisan skills
            'crafting', 'fletching', 'smithing', 'cooking', 'firemaking', 'runecrafting', 'construction',
            # Support skills
            'agility', 'herblore', 'thieving', 'slayer'
        ]
    
    def test_single_skill(self, skill):
        """Test hovering over a single skill"""
        try:
            print(f"\n🎯 Testing skill: {skill.title()}")
            print("-" * 30)
            
            # Start paused for positioning
            print("⏸️  PAUSED - Click into your game screen and press 'p' to test this skill")
            
            # Import keyboard listener
            from pynput import keyboard
            
            is_paused = True
            
            def on_key_press(key):
                nonlocal is_paused
                try:
                    if key.char == 'p':
                        is_paused = False
                        print("▶️  UNPAUSED - Testing skill...")
                        return False  # Stop listener
                except AttributeError:
                    pass
            
            # Start keyboard listener
            listener = keyboard.Listener(on_press=on_key_press)
            listener.start()
            
            # Wait for unpause
            while is_paused:
                time.sleep(0.1)
            
            listener.stop()
            
            # Test the skill
            result = self.functions.checkstats(skill)
            
            if result:
                print(f"✅ {skill.title()} - SUCCESS")
                self.test_results[skill] = True
            else:
                print(f"❌ {skill.title()} - FAILED")
                self.test_results[skill] = False
            
            return result
            
        except Exception as e:
            print(f"❌ Error testing {skill}: {e}")
            self.test_results[skill] = False
            return False
    
    def test_all_skills_auto(self):
        """Test all skills automatically (requires being in stats page)"""
        print("🚀 Auto Testing All Skills")
        print("=" * 50)
        print("⚠️  Make sure you:")
        print("   1. Have RuneScape stats page open (press '4')")
        print("   2. Are ready for rapid skill testing")
        print()
        
        input("Press Enter when ready to start auto testing...")
        
        successful = 0
        failed = 0
        
        for i, skill in enumerate(self.all_skills, 1):
            print(f"\n🔍 Testing {i}/{len(self.all_skills)}: {skill.title()}")
            
            try:
                # Capture screen
                screen = self.functions.capture_screen()
                if screen is None:
                    print(f"❌ Could not capture screen for {skill}")
                    self.test_results[skill] = False
                    failed += 1
                    continue
                
                # Find skill position
                skill_position = self.functions.find_skill_position(screen, skill)
                
                if skill_position:
                    # Move to skill and hover briefly
                    target_x, target_y = skill_position
                    
                    # Quick movement to skill
                    import pyautogui
                    pyautogui.moveTo(target_x, target_y, duration=0.2)
                    
                    # Brief hover
                    time.sleep(0.3)
                    
                    # Move mouse away to clear any popups/tooltips
                    screen_width, screen_height = pyautogui.size()
                    clear_x = max(50, target_x - 200)  # Move left to clear popup
                    clear_y = target_y
                    pyautogui.moveTo(clear_x, clear_y, duration=0.1)
                    
                    print(f"✅ {skill.title()} - Found and hovered")
                    self.test_results[skill] = True
                    successful += 1
                else:
                    print(f"❌ {skill.title()} - Not found")
                    self.test_results[skill] = False
                    failed += 1
                
                # Longer delay between skills to let popups disappear
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error testing {skill}: {e}")
                self.test_results[skill] = False
                failed += 1
        
        print(f"\n📊 Auto Test Complete: {successful} successful, {failed} failed")
        
        # Retry failed skills
        if failed > 0:
            failed_skills = [skill for skill, result in self.test_results.items() if not result]
            print(f"\n🔄 Retrying {len(failed_skills)} failed skills to clear popup interference...")
            
            # Move mouse away from stats area first
            import pyautogui
            pyautogui.moveTo(100, 100, duration=0.3)
            time.sleep(1)
            
            retry_successful = 0
            for skill in failed_skills:
                print(f"\n🔄 Retry: {skill.title()}")
                
                try:
                    screen = self.functions.capture_screen()
                    if screen is None:
                        continue
                    
                    skill_position = self.functions.find_skill_position(screen, skill)
                    
                    if skill_position:
                        target_x, target_y = skill_position
                        pyautogui.moveTo(target_x, target_y, duration=0.2)
                        time.sleep(0.3)
                        
                        # Clear popup
                        clear_x = max(50, target_x - 200)
                        pyautogui.moveTo(clear_x, target_y, duration=0.1)
                        
                        print(f"✅ {skill.title()} - SUCCESS on retry!")
                        self.test_results[skill] = True
                        retry_successful += 1
                        successful += 1
                        failed -= 1
                    else:
                        print(f"❌ {skill.title()} - Still failed")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ Retry error for {skill}: {e}")
            
            if retry_successful > 0:
                print(f"\n🎉 Retry fixed {retry_successful} additional skills!")
                print(f"📊 Final results: {successful} successful, {failed} failed")
        
        self.print_summary()
    
    def test_all_skills_manual(self):
        """Test all skills with manual pause/unpause for each"""
        print("🎮 Manual Testing All Skills")
        print("=" * 50)
        print("This will test each skill individually with pause/unpause")
        print()
        
        successful = 0
        failed = 0
        
        for i, skill in enumerate(self.all_skills, 1):
            print(f"\n--- Skill {i}/{len(self.all_skills)} ---")
            
            # Ask if user wants to test this skill
            user_input = input(f"Test {skill.title()}? (y/n/q to quit): ").lower().strip()
            
            if user_input in ['q', 'quit']:
                print("👋 Stopping skill tests")
                break
            elif user_input in ['y', 'yes', '']:
                success = self.test_single_skill(skill)
                if success:
                    successful += 1
                else:
                    failed += 1
            else:
                print(f"⏭️ Skipping {skill.title()}")
                continue
        
        print(f"\n📊 Manual Test Complete: {successful} successful, {failed} failed")
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        if not self.test_results:
            print("No tests were run.")
            return
        
        print("\n" + "=" * 60)
        print("📊 SKILL TESTING SUMMARY")
        print("=" * 60)
        
        # Group results
        successful_skills = [skill for skill, result in self.test_results.items() if result]
        failed_skills = [skill for skill, result in self.test_results.items() if not result]
        
        print("\n✅ SUCCESSFUL SKILLS:")
        for skill in successful_skills:
            print(f"   ✅ {skill.title()}")
        
        if failed_skills:
            print("\n❌ FAILED SKILLS:")
            for skill in failed_skills:
                print(f"   ❌ {skill.title()}")
        
        print(f"\n📈 Results: {len(successful_skills)}/{len(self.test_results)} skills working")
        
        if len(successful_skills) == len(self.test_results):
            print("🎉 All tested skills working perfectly!")
        elif failed_skills:
            print(f"⚠️  {len(failed_skills)} skill(s) need template improvements:")
            for skill in failed_skills:
                print(f"   💡 Check/recreate images/skills/{skill}.png")


def main():
    """Main function"""
    print("🧪 All Skills Tester")
    print("=" * 50)
    print("Test all 23 RuneScape skills with random hover positioning")
    print()
    
    # Check if required packages are available
    try:
        import cv2
        import numpy as np
        import pyautogui
        from pynput import keyboard
        print("✅ All required packages available")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Install with: pip install opencv-python numpy pyautogui pynput")
        return
    
    tester = AllSkillsTester()
    
    print(f"\n📋 Will test {len(tester.all_skills)} skills:")
    for i, skill in enumerate(tester.all_skills, 1):
        print(f"   {i:2d}. {skill.title()}")
    
    print("\nChoose testing mode:")
    print("1. Manual mode (pause/unpause for each skill)")
    print("2. Auto mode (rapid testing, requires stats page open)")
    print("3. Test specific skill only")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        tester.test_all_skills_manual()
    
    elif choice == '2':
        tester.test_all_skills_auto()
    
    elif choice == '3':
        print(f"\nAvailable skills: {', '.join(tester.all_skills)}")
        skill = input("Enter skill name: ").strip().lower()
        
        if skill in tester.all_skills:
            tester.test_single_skill(skill)
            tester.print_summary()
        else:
            print(f"❌ Invalid skill: {skill}")
    
    elif choice == '4':
        print("👋 Goodbye!")
        return
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
