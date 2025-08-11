#!/usr/bin/env python3
"""
Quick Test - Fast tree detection test
Just detects trees and shows results, no clicking
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tree_detector import detect_tree_indicators, capture_screen
import cv2
import numpy as np

def quick_test():
    """Quick test of tree detection"""
    print("🌳 Quick Tree Detection Test")
    print("=" * 40)
    print("Make sure:")
    print("• RuneLite is open with Tree Indicator plugin enabled")
    print("• Trees are visible on screen")
    print("• Trees are highlighted with green overlays")
    print()
    
    input("Press Enter when ready...")
    
    print("\n📸 Capturing screen...")
    screen = capture_screen()
    if screen is None:
        print("❌ Failed to capture screen")
        return
    
    print("🔍 Analyzing for tree indicators...")
    trees = detect_tree_indicators()
    
    if trees:
        print(f"\n✅ SUCCESS! Found {len(trees)} trees")
        print("\nTree details:")
        for i, tree in enumerate(trees[:5]):  # Show top 5
            x, y = tree['position']
            area = tree['area']
            print(f"  {i+1}. Position: ({x:3d}, {y:3d}) - Area: {area:3d} pixels")
        
        if len(trees) > 5:
            print(f"  ... and {len(trees) - 5} more trees")
    else:
        print("\n❌ No trees detected")
        print("\nTroubleshooting:")
        print("• Check if Tree Indicator plugin is enabled")
        print("• Verify trees are visible and highlighted")
        print("• Make sure you're using default green color")

if __name__ == "__main__":
    quick_test()

