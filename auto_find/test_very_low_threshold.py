#!/usr/bin/env python3
"""
Test tunnel detection with very low threshold to see what we can detect
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from template_finder import findtextonscreen

def test_with_low_threshold():
    """Test all tunnel templates with very low threshold"""
    print("🔍 Testing Tunnel Detection with Very Low Threshold")
    print("=" * 60)
    
    # Test with much lower thresholds
    thresholds = [0.30, 0.25, 0.20, 0.15]
    tunnel_templates = ["tunnel", "tunnel1", "tunnel2", "tunnel3"]
    
    for threshold in thresholds:
        print(f"\n🎯 Testing with threshold: {threshold} ({threshold*100}%)")
        print("-" * 50)
        
        for template_name in tunnel_templates:
            print(f"\n  Testing {template_name}.png...")
            
            result = findtextonscreen(
                template_name, 
                click=False,  # Don't click, just find
                pause=True, 
                confidence_threshold=threshold
            )
            
            if result['success']:
                print(f"  ✅ FOUND: {template_name} at {result['position']} (confidence: {result['confidence']:.3f})")
                return  # Stop at first success
            else:
                print(f"  ❌ {template_name}: Below {threshold}")
        
        print(f"\n  No matches found at {threshold} threshold")
    
    print(f"\n❌ No tunnel templates matched even at 0.15 threshold")
    print(f"💡 The tunnel text in your current view is likely very different from the templates")

if __name__ == "__main__":
    test_with_low_threshold()
