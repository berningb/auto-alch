#!/usr/bin/env python3
"""
Tree Bot Launcher - Easy access to all tree automation tools
Main entry point for all tree-related automation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main launcher menu"""
    print("🌳 Tree Bot - Complete Woodcutting Automation")
    print("=" * 60)
    print("All-in-one toolkit for automated tree detection and chopping")
    print()
    print("🤖 Available Tools:")
    print()
    print("1. 🪓 Tree Chopping Loop (MAIN BOT)")
    print("   └ Fully automated woodcutting loop")
    print("   └ Clicks trees → waits for chop → finds next tree")
    print()
    print("2. 🔍 Tree Detector (Testing)")
    print("   └ Test tree detection and single clicks")
    print("   └ Debug mode for troubleshooting")
    print()
    print("3. 🎨 Color Calibrator (Setup)")
    print("   └ Find exact HSV values for your tree indicators")
    print("   └ Use this if trees aren't being detected")
    print()
    print("4. ⚡ Quick Test")
    print("   └ Fast detection test without menus")
    print()
    print("5. 📖 Help & Setup")
    print()
    print("6. 🚪 Exit")
    print()
    
    choice = input("Enter choice (1-6): ").strip()
    
    if choice == '1':
        print("\n🪓 Launching Tree Chopping Loop...")
        print("=" * 40)
        try:
            from tree_chopping_loop import TreeChoppingBot, setup_pause_controls
            from pynput import keyboard
            
            bot = TreeChoppingBot()
            listener = setup_pause_controls(bot)
            listener.start()
            
            try:
                bot.run_chopping_loop()
            finally:
                listener.stop()
        except ImportError as e:
            print(f"❌ Error importing: {e}")
            print("Make sure all required packages are installed")
        except Exception as e:
            print(f"❌ Error running chopping loop: {e}")
        
    elif choice == '2':
        print("\n🔍 Launching Tree Detector...")
        print("=" * 30)
        try:
            import tree_detector
            tree_detector.main()
        except ImportError as e:
            print(f"❌ Error importing tree_detector: {e}")
        except Exception as e:
            print(f"❌ Error running tree detector: {e}")
        
    elif choice == '3':
        print("\n🎨 Launching Color Calibrator...")
        print("=" * 35)
        try:
            import calibrate_color
            calibrate_color.main()
        except ImportError as e:
            print(f"❌ Error importing calibrate_color: {e}")
        except Exception as e:
            print(f"❌ Error running color calibrator: {e}")
        
    elif choice == '4':
        print("\n⚡ Running Quick Test...")
        print("=" * 25)
        try:
            import quick_test
            quick_test.quick_test()
        except ImportError as e:
            print(f"❌ Error importing quick_test: {e}")
        except Exception as e:
            print(f"❌ Error running quick test: {e}")
        
    elif choice == '5':
        show_help()
        
    elif choice == '6':
        print("👋 Goodbye!")
        return
        
    else:
        print("❌ Invalid choice")

def show_help():
    """Show setup instructions and help"""
    print("\n📖 Setup & Help Guide")
    print("=" * 50)
    print()
    print("🔧 PREREQUISITES:")
    print("=" * 20)
    print("1. RuneLite with Fiish's Tree Indicator plugin installed")
    print("2. Python packages: pip install opencv-python pyautogui numpy pynput")
    print("3. Tree Indicator plugin enabled and configured")
    print()
    print("⚙️  TREE INDICATOR SETUP:")
    print("=" * 25)
    print("• Enable: ✅ Tree Indicator plugin")
    print("• Color: Default green (RGB 0,200,120) recommended")
    print("• Mode: Either 'Tile' or 'Full Tree' works")
    print("• Stroke Width: 2-3 pixels")
    print("• Fill: Optional (both work)")
    print("• Tree Types: Enable the types you want to chop")
    print()
    print("🎮 USAGE WORKFLOW:")
    print("=" * 20)
    print("1. Position your character in a woodcutting area")
    print("2. Make sure trees are visible and highlighted green")
    print("3. Run Quick Test (#4) to verify detection works")
    print("4. If no detection, use Color Calibrator (#3)")
    print("5. Once detection works, use Tree Chopping Loop (#1)")
    print()
    print("🎯 RECOMMENDED AREAS:")
    print("=" * 22)
    print("• Lumbridge: Regular trees (level 1)")
    print("• Draynor: Willow trees (level 30)")
    print("• Seers Village: Maple trees (level 45)")
    print("• Falador: Yew trees (level 60)")
    print("• Varrock: Multiple tree types")
    print()
    print("🛡️  SAFETY FEATURES:")
    print("=" * 20)
    print("• Press 'p' to pause/unpause anytime")
    print("• Press 'q' to quit safely")
    print("• Ctrl+C for emergency stop")
    print("• Random delays and offsets")
    print("• Timeout protection")
    print()
    print("🐛 TROUBLESHOOTING:")
    print("=" * 20)
    print("• No trees detected → Use Color Calibrator")
    print("• Trees detected but not clicked → Check game window focus")
    print("• Bot stops working → Check if trees are still highlighted")
    print("• False clicks → Adjust HSV range or min area")
    print()
    print("📁 FILES:")
    print("=" * 10)
    print("• tree_chopping_loop.py - Main automation bot")
    print("• tree_detector.py - Detection testing and debugging")
    print("• calibrate_color.py - Color calibration tool")
    print("• quick_test.py - Fast detection verification")
    print("• README.md - Detailed documentation")
    print()
    
    input("Press Enter to return to main menu...")

if __name__ == "__main__":
    main()
