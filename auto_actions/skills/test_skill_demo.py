#!/usr/bin/env python3
"""
Demo script for testSkill function
"""

import sys
import os

# Add the parent directory to Python path so we can import test_skill
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from skills.test_skill import testSkill


def main():
    """Demo the testSkill function"""
    print("🧪 TestSkill Function Demo")
    print("=" * 50)
    
    # Example 1: Test single skill with improved retry logic
    print("\n📋 Example 1: Test single skill (magic) with retry logic")
    print("-" * 40)
    results1 = testSkill(['magic'], hover_duration_range=(2, 3), interactive=True)
    print(f"Results: {results1}")
    
    # Example 2: Test multiple skills
    print("\n📋 Example 2: Test multiple skills")
    print("-" * 40)
    skills_to_test = ['magic', 'attack', 'strength']
    results2 = testSkill(skills_to_test, hover_duration_range=(1, 2), interactive=True)
    print(f"Results: {results2}")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()

