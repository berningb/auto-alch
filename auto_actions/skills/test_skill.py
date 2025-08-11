#!/usr/bin/env python3
"""
Test Skill Function - Test specific skills with hover timing
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
except ImportError as e:
    print(f"❌ Error importing functions: {e}")
    print("Make sure funcs.py exists in the same directory")
    sys.exit(1)


def testSkill(skills_to_test, hover_duration_range=(2, 5), interactive=False):
    """
    Test specific skills with hover timing
    
    Args:
        skills_to_test (list): List of skill names to test (e.g., ['magic', 'attack'])
        hover_duration_range (tuple): Range of seconds to hover on each skill (min, max)
        interactive (bool): Whether to pause for user input before each skill
    
    Returns:
        dict: Results dictionary with success/failure for each skill
    """
    functions = AutoActionFunctions()
    test_results = {}
    
    # All 23 RuneScape skills for validation
    all_skills = [
        # Combat skills
        'attack', 'strength', 'defence', 'hitpoints', 'prayer', 'ranged', 'magic',
        # Gathering skills  
        'mining', 'fishing', 'woodcutting', 'farming', 'hunter',
        # Artisan skills
        'crafting', 'fletching', 'smithing', 'cooking', 'firemaking', 'runecrafting', 'construction',
        # Support skills
        'agility', 'herblore', 'thieving', 'slayer'
    ]
    
    # Validate skills
    valid_skills = []
    invalid_skills = []
    
    for skill in skills_to_test:
        if skill.lower() in all_skills:
            valid_skills.append(skill.lower())
        else:
            invalid_skills.append(skill)
    
    if invalid_skills:
        print(f"⚠️  Invalid skills: {invalid_skills}")
        print(f"Valid skills: {', '.join(all_skills)}")
    
    if not valid_skills:
        print("❌ No valid skills to test")
        return test_results
    
    print(f"🎯 Testing {len(valid_skills)} skills: {', '.join(valid_skills)}")
    print(f"⏱️  Hover duration: {hover_duration_range[0]}-{hover_duration_range[1]} seconds per skill")
    
    for i, skill in enumerate(valid_skills, 1):
        print(f"\n--- Testing {i}/{len(valid_skills)}: {skill.title()} ---")
        
        try:
            # Interactive pause if requested
            if interactive:
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
            
            # Test the skill using improved checkstats function
            print(f"🔍 Testing {skill.title()}...")
            
            # Try multiple times with different methods
            success = False
            max_attempts = 3
            
            for attempt in range(max_attempts):
                print(f"   🔄 Attempt {attempt + 1}/{max_attempts}")
                
                # Use keybind method for first attempt, tab for others
                method = 'keybind' if attempt == 0 else 'tab'
                
                result = functions.checkstats(skill, method=method, interactive=False)
                
                if result:
                    success = True
                    break
                else:
                    print(f"   ❌ Attempt {attempt + 1} failed, trying again...")
                    time.sleep(1)  # Brief pause between attempts
            
            if success:
                # Get hover duration
                hover_duration = random.uniform(hover_duration_range[0], hover_duration_range[1])
                print(f"✅ {skill.title()} - SUCCESS, hovering for {hover_duration:.1f}s")
                
                # Hover for the specified duration
                time.sleep(hover_duration)
                
                # Move mouse away to clear any popups
                import pyautogui
                current_x, current_y = pyautogui.position()
                clear_x = max(50, current_x - 200)  # Move left to clear popup
                pyautogui.moveTo(clear_x, current_y, duration=0.2)
                
                test_results[skill] = True
            else:
                print(f"❌ {skill.title()} - FAILED after {max_attempts} attempts")
                test_results[skill] = False
            
        except Exception as e:
            print(f"❌ Error testing {skill}: {e}")
            test_results[skill] = False
    
    # Print summary
    successful_skills = [skill for skill, result in test_results.items() if result]
    failed_skills = [skill for skill, result in test_results.items() if not result]
    
    print(f"\n📊 Test Complete: {len(successful_skills)} successful, {len(failed_skills)} failed")
    
    if successful_skills:
        print(f"✅ Successful: {', '.join(successful_skills)}")
    
    if failed_skills:
        print(f"❌ Failed: {', '.join(failed_skills)}")
    
    return test_results


def main():
    """Main function for standalone testing"""
    print("🧪 Skill Tester")
    print("=" * 50)
    
    # Example usage
    skills_to_test = ['magic', 'attack', 'strength']
    results = testSkill(skills_to_test, hover_duration_range=(2, 5), interactive=True)
    
    print(f"\nFinal results: {results}")


if __name__ == "__main__":
    main()

