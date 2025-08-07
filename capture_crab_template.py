import cv2
import numpy as np
import pyautogui
import time

# Configure pyautogui for safety
pyautogui.FAILSAFE = True  # Move mouse to corner to stop

def capture_crab_template():
    """Capture the gemstone crab template by user positioning"""
    print("🦀 Gemstone Crab Template Capture")
    print("=" * 40)
    print("Please move your mouse over the Gemstone Crab (with blue outline) and press Enter...")
    print("Make sure the crab is clearly visible with its blue outline!")
    input("Press Enter when mouse is over the Gemstone Crab...")
    
    x, y = pyautogui.position()
    
    # Capture a region around the mouse position (crab is larger)
    try:
        screenshot = pyautogui.screenshot(region=(x-40, y-30, 80, 60))
        template = np.array(screenshot)
        template = cv2.cvtColor(template, cv2.COLOR_RGB2BGR)
        
        # Save template for later use
        cv2.imwrite("crab_template.png", template)
        
        print(f"📍 Gemstone Crab template captured at ({x}, {y})")
        print("✅ Template saved as 'crab_template.png'")
        print("You can now run the main script!")
        return True
    except Exception as e:
        print(f"Error capturing crab template: {e}")
        return False

if __name__ == "__main__":
    capture_crab_template()
