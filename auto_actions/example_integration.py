#!/usr/bin/env python3
"""
Example Integration Script
Shows how to use the funcs.py module in your other auto scripts
"""

import sys
import os
import time
import random

# Add the auto_actions directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    # Import your functions module
    from funcs import AutoActionFunctions, checkstats
    print("✅ Successfully imported auto functions")
except ImportError as e:
    print(f"❌ Error importing functions: {e}")
    sys.exit(1)

# You can also import functions from your existing auto_alch script
auto_alch_dir = os.path.join(os.path.dirname(current_dir), "auto_alch")
sys.path.append(auto_alch_dir)


class IntegratedAutoScript:
    """
    Example of how to integrate the functions module with other auto scripts
    """
    
    def __init__(self):
        # Initialize the auto functions
        self.auto_functions = AutoActionFunctions()
        self.is_running = False
        
        print("🤖 Integrated Auto Script initialized")
        print("📚 Available functions from funcs.py:")
        print("   - checkstats(skill_name)")
        print("   - capture_screen()")
        print("   - press_key(key, description)")
        print("   - human_click(position, action_name)")
        print("   - find_template(screen, template, threshold)")
    
    def example_stats_monitoring(self):
        """
        Example: Monitor multiple skills during training
        """
        print("\n📊 Example: Stats Monitoring")
        print("This demonstrates checking multiple skills")
        
        skills_to_monitor = ['magic', 'hitpoints', 'defence']
        
        for skill in skills_to_monitor:
            print(f"\n🔍 Checking {skill}...")
            success = self.auto_functions.checkstats(skill)
            
            if success:
                print(f"✅ Successfully checked {skill}")
                # Wait between checks
                time.sleep(random.uniform(2, 4))
            else:
                print(f"❌ Failed to check {skill}")
                break
    
    def example_with_breaks(self):
        """
        Example: Using functions with break logic (similar to auto_alch)
        """
        print("\n⏰ Example: Training with Stats Breaks")
        print("This demonstrates checking stats periodically during training")
        
        # Simulate training session
        training_skill = 'magic'
        check_interval = 5  # Check stats every 5 actions
        action_count = 0
        max_actions = 15  # Limit for demo
        
        print(f"🎯 Starting training session for {training_skill}")
        print(f"📊 Will check stats every {check_interval} actions")
        
        while action_count < max_actions:
            # Simulate training action
            action_count += 1
            print(f"   🔥 Training action {action_count}/{max_actions}")
            
            # Simulate action delay
            time.sleep(random.uniform(1, 2))
            
            # Check stats periodically
            if action_count % check_interval == 0:
                print(f"\n📊 Time for stats check! (after {action_count} actions)")
                stats_success = self.auto_functions.checkstats(training_skill)
                
                if stats_success:
                    print("✅ Stats check completed, continuing training...")
                    # Return to training interface (example)
                    self.auto_functions.press_key('3', "return to spellbook")
                    time.sleep(1)
                else:
                    print("❌ Stats check failed, stopping session")
                    break
        
        print(f"\n🏁 Training session completed! ({action_count} actions)")
    
    def example_convenience_function(self):
        """
        Example: Using the convenience function for quick stats checks
        """
        print("\n🚀 Example: Quick Stats Check")
        print("Using the convenience function for simple stats checking")
        
        # Use the standalone function (no need to create class instance)
        skill = 'attack'
        print(f"🎯 Quick check of {skill} skill...")
        
        success = checkstats(skill)  # This is the convenience function
        
        if success:
            print("✅ Quick stats check completed!")
        else:
            print("❌ Quick stats check failed!")
    
    def example_screen_analysis(self):
        """
        Example: Analyzing screen content
        """
        print("\n🔍 Example: Screen Analysis")
        print("Demonstrating screen capture and analysis")
        
        # Capture current screen
        screen = self.auto_functions.capture_screen()
        
        if screen is not None:
            print(f"✅ Screen captured: {screen.shape}")
            
            # Example: Check if stats template is visible
            if self.auto_functions.stats_template is not None:
                stats_pos, confidence = self.auto_functions.find_template(
                    screen, 
                    self.auto_functions.stats_template, 
                    threshold=0.6
                )
                
                if stats_pos:
                    print(f"📊 Stats interface detected at {stats_pos} (confidence: {confidence:.2f})")
                else:
                    print(f"❌ Stats interface not found (best match: {confidence:.2f})")
            else:
                print("⚠️ No stats template loaded for comparison")
        else:
            print("❌ Failed to capture screen")
    
    def run_examples(self):
        """Run all examples"""
        print("🎮 Running Integration Examples")
        print("=" * 50)
        
        examples = [
            ("Quick Stats Check", self.example_convenience_function),
            ("Screen Analysis", self.example_screen_analysis),
            ("Stats Monitoring", self.example_stats_monitoring),
            ("Training with Stats Breaks", self.example_with_breaks),
        ]
        
        for i, (name, func) in enumerate(examples, 1):
            print(f"\n--- Example {i}: {name} ---")
            
            # Ask user if they want to run this example
            user_input = input(f"Run '{name}' example? (y/n/q to quit): ").lower().strip()
            
            if user_input in ['q', 'quit']:
                print("👋 Exiting examples")
                break
            elif user_input in ['y', 'yes']:
                try:
                    func()
                    print(f"✅ Example '{name}' completed")
                except Exception as e:
                    print(f"❌ Example '{name}' failed: {e}")
                
                # Pause between examples
                if i < len(examples):
                    input("\nPress Enter to continue to next example...")
            else:
                print(f"⏭️ Skipping '{name}' example")


def main():
    """Main function"""
    print("🔗 Auto Functions Integration Example")
    print("=" * 50)
    print("This script demonstrates how to integrate funcs.py with other scripts")
    print()
    
    # Check dependencies
    try:
        import cv2
        import numpy as np
        import pyautogui
        print("✅ All dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install opencv-python numpy pyautogui")
        return
    
    print("\nChoose an option:")
    print("1. Run all integration examples")
    print("2. Quick stats check only")
    print("3. Screen analysis only")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        script = IntegratedAutoScript()
        script.run_examples()
    
    elif choice == '2':
        skill = input("Enter skill name (default: magic): ").strip() or 'magic'
        print(f"🎯 Quick checking {skill}...")
        success = checkstats(skill)
        if success:
            print("✅ Quick stats check completed!")
        else:
            print("❌ Quick stats check failed!")
    
    elif choice == '3':
        script = IntegratedAutoScript()
        script.example_screen_analysis()
    
    elif choice == '4':
        print("👋 Goodbye!")
        return
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
