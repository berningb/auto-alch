#!/usr/bin/env python3
"""
Auto Find - Simple Color-Based Detection
Detects and clicks on colored text elements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from color_detection import clicktunnel, clickcrab, detect_tunnel, detect_crab, test_both_colors

def main():
    """Main Auto Find interface"""
    print("🎯 Auto Find - Color Detection System")
    print("=" * 50)
    print("Simple, reliable detection using color matching")
    print("🕳️  Tunnel: Green text detection")
    print("🦀 Crab: Cyan text detection")
    print()
    print("Choose action:")
    print("1. Click tunnel (green)")
    print("2. Click crab (cyan)")
    print("3. Detect tunnel only")
    print("4. Detect crab only")
    print("5. Test both detections")
    print("6. Exit")
    print()
    
    choice = input("Enter choice (1-6): ").strip()
    
    if choice == '1':
        print("\n🕳️  Clicking tunnel...")
        result = clicktunnel()
        if result['success']:
            print("✅ Tunnel clicked successfully!")
        else:
            print("❌ Failed to click tunnel")
    
    elif choice == '2':
        print("\n🦀 Clicking crab...")
        result = clickcrab()
        if result['success']:
            print("✅ Crab clicked successfully!")
        else:
            print("❌ Failed to click crab")
    
    elif choice == '3':
        print("\n🕳️  Detecting tunnel...")
        result = detect_tunnel()
        if result and result['success']:
            print(f"✅ Tunnel found at {result['position']}")
        else:
            print("❌ No tunnel detected")
    
    elif choice == '4':
        print("\n🦀 Detecting crab...")
        result = detect_crab()
        if result and result['success']:
            print(f"✅ Crab found at {result['position']}")
        else:
            print("❌ No crab detected")
    
    elif choice == '5':
        print("\n🎨 Testing both detections...")
        test_both_colors()
    
    elif choice == '6':
        print("👋 Goodbye!")
        return
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
