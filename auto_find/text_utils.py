#!/usr/bin/env python3
"""
Text Detection Utilities
Simple utilities for finding and clicking text on screen
"""

import sys
import os
import time
import random

# Add the auto_actions directory to Python path so we can import funcs
auto_actions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auto_actions')
sys.path.append(auto_actions_dir)

try:
    import cv2
    import numpy as np
    import pyautogui
    import pytesseract
    from pynput import keyboard
    from funcs import AutoActionFunctions
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    sys.exit(1)


# Global instance for easy access
_auto_functions = None

def get_auto_functions():
    """Get or create AutoActionFunctions instance"""
    global _auto_functions
    if _auto_functions is None:
        _auto_functions = AutoActionFunctions()
    return _auto_functions


def wait_for_unpause():
    """Wait for user to press 'p' to continue"""
    print("⏸️  PAUSED - Click into your game screen and press 'p' to start")
    
    is_paused = True
    
    def on_key_press(key):
        nonlocal is_paused
        try:
            if key.char == 'p':
                is_paused = False
                print("▶️  UNPAUSED - Starting action...")
                return False  # Stop listener
        except AttributeError:
            pass
    
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()
    
    while is_paused:
        time.sleep(0.1)
    
    listener.stop()


def findtextonscreen(target_text, click=True, pause=True, confidence_threshold=0.5, case_sensitive=False):
    """
    Find specific text on screen using OCR and optionally click on it
    
    Args:
        target_text (str): The text to search for
        click (bool): Whether to click on the found text (default: True)
        pause (bool): Whether to pause and wait for 'p' key before starting (default: True)
        confidence_threshold (float): Minimum confidence for text detection 0.0-1.0 (default: 0.5)
        case_sensitive (bool): Whether search should be case sensitive (default: False)
        
    Returns:
        dict: Result with keys:
            - success (bool): Whether text was found and action completed
            - text_found (str): The actual text that was found 
            - position (tuple): (x, y) coordinates where text was found
            - confidence (float): OCR confidence level
            - error (str): Error message if failed
    """
    
    if pause:
        print(f"🔍 Preparing to search for: '{target_text}'")
        wait_for_unpause()
    
    try:
        print(f"🔍 Searching for text: '{target_text}'")
        
        # Get AutoActionFunctions instance
        functions = get_auto_functions()
        
        # Capture screen
        screen = functions.capture_screen()
        if screen is None:
            return {
                'success': False,
                'error': 'Failed to capture screen',
                'position': None,
                'confidence': 0
            }
        
        # Convert BGR to RGB for tesseract
        screen_rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
        
        # Use tesseract to extract text with bounding boxes
        data = pytesseract.image_to_data(screen_rgb, output_type=pytesseract.Output.DICT)
        
        # Prepare search text
        search_text = target_text if case_sensitive else target_text.lower()
        
        # Find all matches
        found_matches = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:
                continue
            
            # Apply case sensitivity
            compare_text = text if case_sensitive else text.lower()
            
            # Check if target text is in detected text
            confidence = float(data['conf'][i]) / 100.0  # Convert to 0-1 scale
            
            if search_text in compare_text and confidence >= confidence_threshold:
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                center_x = x + w // 2
                center_y = y + h // 2
                
                match = {
                    'text': text,
                    'position': (center_x, center_y),
                    'confidence': confidence,
                    'bounding_box': (x, y, w, h)
                }
                found_matches.append(match)
                
                print(f"✅ Found '{text}' at ({center_x}, {center_y}) (confidence: {confidence:.2f})")
        
        if not found_matches:
            error_msg = f"Text '{target_text}' not found on screen"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'position': None,
                'confidence': 0
            }
        
        # Use the match with highest confidence
        best_match = max(found_matches, key=lambda x: x['confidence'])
        
        print(f"🎯 Best match: '{best_match['text']}' (confidence: {best_match['confidence']:.2f})")
        
        if click:
            # Add some randomness to click position
            x, y = best_match['position']
            offset_x = random.randint(-8, 8)
            offset_y = random.randint(-5, 5)
            final_x = x + offset_x
            final_y = y + offset_y
            
            print(f"🖱️  Moving to ({final_x}, {final_y}) and clicking...")
            pyautogui.moveTo(final_x, final_y, duration=0.3)
            time.sleep(0.1)
            pyautogui.click()
            time.sleep(0.2)  # Brief pause after click
            print(f"✅ Successfully clicked on '{best_match['text']}'")
        
        return {
            'success': True,
            'text_found': best_match['text'],
            'position': best_match['position'],
            'confidence': best_match['confidence'],
            'bounding_box': best_match['bounding_box']
        }
        
    except Exception as e:
        error_msg = f"Error during text detection: {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'position': None,
            'confidence': 0
        }


# Alias for convenience
find_text = findtextonscreen


def quick_test():
    """Quick test function for the findtextonscreen function"""
    print("🧪 Quick Text Detection Test")
    print("=" * 40)
    
    target_text = input("Enter text to search for: ").strip()
    if not target_text:
        print("❌ No text entered")
        return
    
    click_option = input("Click on found text? (y/n, default: y): ").strip().lower()
    should_click = click_option != 'n'
    
    result = findtextonscreen(target_text, click=should_click)
    
    print("\n📊 Result:")
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   Text found: '{result['text_found']}'")
        print(f"   Position: {result['position']}")
        print(f"   Confidence: {result['confidence']:.2f}")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    quick_test()
