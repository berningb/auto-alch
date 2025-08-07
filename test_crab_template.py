#!/usr/bin/env python3
"""
Test script for gemstone crab template functionality
"""

import cv2
import numpy as np
import pyautogui
import time
from simple_template_alch import SimpleTemplateAlch

def test_crab_template():
    """Test the gemstone crab template functionality"""
    print("🦀 Testing Gemstone Crab Template Functionality")
    print("=" * 50)
    
    # Create the clicker instance
    clicker = SimpleTemplateAlch()
    
    # Test template loading
    print("1. Testing template loading...")
    templates_loaded = clicker.load_templates()
    if templates_loaded:
        print("   ✅ All templates loaded successfully")
        print(f"   🔮 Alchemy spell template: {'Loaded' if clicker.alch_spell_template is not None else 'Missing'}")
        print(f"   🏹 Arrow template: {'Loaded' if clicker.arrow_template is not None else 'Missing'}")
        print(f"   🦀 Crab template: {'Loaded' if clicker.crab_template is not None else 'Missing'}")
    else:
        print("   ❌ Some templates are missing")
        return False
    
    # Test screen capture
    print("\n2. Testing screen capture...")
    screen = clicker.capture_screen()
    if screen is not None:
        print("   ✅ Screen capture working")
        print(f"   📏 Screen size: {screen.shape[1]}x{screen.shape[0]}")
    else:
        print("   ❌ Screen capture failed")
        return False
    
    # Test crab detection
    print("\n3. Testing crab detection...")
    crab_position, crab_confidence = clicker.detect_crab(screen)
    if crab_position:
        print(f"   ✅ Crab detected at {crab_position} (confidence: {crab_confidence:.2f})")
    else:
        print(f"   ⚠️ No crab detected (confidence: {crab_confidence:.2f})")
        print("   💡 This is normal if no crab is currently visible on screen")
    
    # Test position saving/loading
    print("\n4. Testing position saving/loading...")
    clicker.crab_position = (100, 200)  # Test position
    clicker.save_positions()
    clicker.crab_position = None  # Clear it
    clicker.load_positions()
    if clicker.crab_position == (100, 200):
        print("   ✅ Position saving/loading working")
    else:
        print("   ❌ Position saving/loading failed")
    
    print("\n✅ All tests completed!")
    print("🎯 The gemstone crab template is ready to use!")
    return True

if __name__ == "__main__":
    test_crab_template()
