#!/usr/bin/env python3
"""
Quick test script to test the checkstats function
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from funcs import checkstats, AutoActionFunctions
    print("✅ Successfully imported functions")
    
    print("\n🧪 Quick Test: checkstats function")
    print("=" * 40)
    
    # Test with magic skill
    skill = 'magic'
    print(f"🎯 Testing checkstats with skill: {skill}")
    print("⚠️  This will:")
    print("   1. Press '4' to open stats")
    print("   2. Move mouse to magic skill position")
    print("   3. Hover over the skill")
    print()
    
    input("Press Enter to start the test (or Ctrl+C to cancel)...")
    
    # Run the test
    result = checkstats(skill)
    
    print(f"\n📊 Test Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    if result:
        print("🎉 The checkstats function worked correctly!")
    else:
        print("😞 The checkstats function encountered an issue.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error during test: {e}")

print("\n👋 Test completed!")
