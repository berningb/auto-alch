#!/usr/bin/env python3
"""
Example Usage of Text Detection
Shows how to use the findtextonscreen function for common tasks
"""

import sys
import os
import time

# Add the current directory to Python path so we can import text_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from text_utils import findtextonscreen
except ImportError as e:
    print(f"❌ Error importing text_utils: {e}")
    print("Make sure text_utils.py is in the same directory")
    sys.exit(1)


def example_npc_interaction():
    """Example: Find and click on an NPC name"""
    print("🧙 NPC Interaction Example")
    print("-" * 30)
    
    npc_name = input("Enter NPC name to find and click: ").strip()
    if not npc_name:
        print("❌ No NPC name entered")
        return
    
    # Find and click on the NPC
    result = findtextonscreen(npc_name, click=True, pause=True)
    
    if result['success']:
        print(f"✅ Successfully interacted with {npc_name}!")
    else:
        print(f"❌ Could not find NPC: {npc_name}")


def example_item_search():
    """Example: Find an item in inventory or interface"""
    print("🎒 Item Search Example")
    print("-" * 30)
    
    item_name = input("Enter item name to find: ").strip()
    if not item_name:
        print("❌ No item name entered")
        return
    
    click_option = input("Click on the item? (y/n): ").strip().lower()
    should_click = click_option == 'y'
    
    # Find the item
    result = findtextonscreen(item_name, click=should_click, pause=True)
    
    if result['success']:
        action = "clicked on" if should_click else "found"
        print(f"✅ Successfully {action} {item_name} at {result['position']}!")
    else:
        print(f"❌ Could not find item: {item_name}")


def example_interface_button():
    """Example: Find and click interface buttons"""
    print("🔘 Interface Button Example")
    print("-" * 30)
    
    button_text = input("Enter button text to find and click: ").strip()
    if not button_text:
        print("❌ No button text entered")
        return
    
    # Find and click the button
    result = findtextonscreen(button_text, click=True, pause=True, confidence_threshold=0.6)
    
    if result['success']:
        print(f"✅ Successfully clicked button: {button_text}!")
    else:
        print(f"❌ Could not find button: {button_text}")


def example_continuous_monitoring():
    """Example: Keep looking for text until it appears"""
    print("👁️ Continuous Monitoring Example")
    print("-" * 30)
    
    target_text = input("Enter text to monitor for: ").strip()
    if not target_text:
        print("❌ No text entered")
        return
    
    max_attempts = input("Max attempts (default: 10): ").strip()
    max_attempts = int(max_attempts) if max_attempts.isdigit() else 10
    
    print(f"🔄 Will check for '{target_text}' up to {max_attempts} times...")
    print("Press Ctrl+C to stop early")
    
    # Wait for initial positioning
    from text_utils import wait_for_unpause
    print("Position your screen and press 'p' to start monitoring...")
    wait_for_unpause()
    
    try:
        for attempt in range(1, max_attempts + 1):
            print(f"\n🔍 Attempt {attempt}/{max_attempts}")
            
            # Search without pausing each time
            result = findtextonscreen(target_text, click=True, pause=False)
            
            if result['success']:
                print(f"🎉 Found and clicked '{target_text}' on attempt {attempt}!")
                break
            else:
                print(f"   Text not found, waiting 2 seconds...")
                time.sleep(2)
        else:
            print(f"❌ Text '{target_text}' never appeared after {max_attempts} attempts")
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")


def main():
    """Main menu for examples"""
    print("🔍 Text Detection Examples")
    print("=" * 40)
    print("Choose an example to run:")
    print()
    print("1. NPC Interaction (find and click NPC)")
    print("2. Item Search (find item in inventory/interface)")
    print("3. Interface Button (find and click buttons)")
    print("4. Continuous Monitoring (keep checking for text)")
    print("5. Custom Search")
    print("6. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == '1':
            example_npc_interaction()
        elif choice == '2':
            example_item_search()
        elif choice == '3':
            example_interface_button()
        elif choice == '4':
            example_continuous_monitoring()
        elif choice == '5':
            # Custom search
            text = input("Enter text to search for: ").strip()
            if text:
                result = findtextonscreen(text, click=True)
                print(f"Result: {result}")
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")
        
        print("\n" + "="*40)


if __name__ == "__main__":
    main()
