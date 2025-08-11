import cv2
import numpy as np
import pyautogui
import time

def test_color_detection():
    print("🔍 Testing crab color detection...")
    print("Please position your mouse over the crab and press Enter...")
    input()
    
    # Capture screen
    screen = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    
    # Get mouse position
    mouse_x, mouse_y = pyautogui.position()
    print(f"Mouse position: ({mouse_x}, {mouse_y})")
    
    # Get color at mouse position
    bgr_color = screen[mouse_y, mouse_x]
    print(f"BGR color at mouse: {bgr_color}")
    
    # Convert to HSV
    hsv_color = cv2.cvtColor(np.array([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0]
    print(f"HSV color at mouse: {hsv_color}")
    
    # Test different HSV ranges
    h, s, v = hsv_color
    
    # Original ranges (cyan)
    ranges_to_test = [
        ("Original (cyan)", np.array([80, 120, 120]), np.array([100, 255, 255])),
        ("New (magenta)", np.array([140, 155, 155]), np.array([160, 255, 255])),
        ("Wide magenta", np.array([130, 100, 100]), np.array([170, 255, 255])),
        ("Very wide", np.array([120, 50, 50]), np.array([180, 255, 255])),
        ("Around actual", np.array([max(0, h-10), max(0, s-50), max(0, v-50)]), 
         np.array([min(179, h+10), min(255, s+50), min(255, v+50)])),
        ("Wide around actual", np.array([max(0, h-20), max(0, s-100), max(0, v-100)]), 
         np.array([min(179, h+20), min(255, s+100), min(255, v+100)])),
    ]
    
    for name, lower, upper in ranges_to_test:
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        
        # Count non-zero pixels
        non_zero = cv2.countNonZero(mask)
        total_pixels = mask.shape[0] * mask.shape[1]
        percentage = (non_zero / total_pixels) * 100
        
        print(f"{name}: {non_zero} pixels ({percentage:.2f}%) - Range: {lower} to {upper}")
        
        # Check if mouse position is detected
        if mask[mouse_y, mouse_x] > 0:
            print(f"  ✅ Mouse position detected!")
        else:
            print(f"  ❌ Mouse position NOT detected")
    
    # Save debug images
    cv2.imwrite("debug_screen.png", screen)
    print("Saved debug_screen.png")
    
    # Create a small region around mouse for detailed analysis
    x1, y1 = max(0, mouse_x-50), max(0, mouse_y-50)
    x2, y2 = min(screen.shape[1], mouse_x+50), min(screen.shape[0], mouse_y+50)
    region = screen[y1:y2, x1:x2]
    cv2.imwrite("debug_region.png", region)
    print("Saved debug_region.png")
    
    # Test the "around actual" range more thoroughly
    h, s, v = hsv_color
    test_lower = np.array([max(0, h-20), max(0, s-100), max(0, v-100)])
    test_upper = np.array([min(179, h+20), min(255, s+100), min(255, v+100)])
    
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, test_lower, test_upper)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"\nFound {len(contours)} contours with 'around actual' range")
    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        print(f"  Contour {i+1}: area={area:.0f}, bbox=({x},{y},{w},{h})")
        
        # Check if mouse is in this contour
        if cv2.pointPolygonTest(c, (mouse_x, mouse_y), False) >= 0:
            print(f"    ✅ Mouse is inside this contour!")

if __name__ == "__main__":
    test_color_detection()

