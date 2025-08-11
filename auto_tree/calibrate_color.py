#!/usr/bin/env python3
"""
Color Calibration Tool - Find the exact HSV range for your tree indicators
Click on tree indicators to analyze their color and calibrate the detection
"""

import cv2
import numpy as np
import pyautogui
from pynput import mouse
import sys
import os

class ColorCalibrator:
    def __init__(self):
        self.screen = None
        self.hsv = None
        self.clicked_colors = []
        self.running = False
        
    def capture_screen(self):
        """Capture current screen"""
        try:
            image = pyautogui.screenshot()
            self.screen = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            self.hsv = cv2.cvtColor(self.screen, cv2.COLOR_BGR2HSV)
            return True
        except Exception as e:
            print(f"❌ Error capturing screen: {e}")
            return False
    
    def on_click(self, x, y, button, pressed):
        """Handle mouse clicks"""
        if pressed and button == mouse.Button.left and self.hsv is not None:
            # Get color at clicked position
            bgr_color = self.screen[y, x]
            hsv_color = self.hsv[y, x]
            
            # Convert BGR to RGB for display
            rgb_color = (int(bgr_color[2]), int(bgr_color[1]), int(bgr_color[0]))
            
            print(f"\n🎯 Clicked at ({x}, {y})")
            print(f"RGB: {rgb_color}")
            print(f"HSV: ({hsv_color[0]}, {hsv_color[1]}, {hsv_color[2]})")
            
            self.clicked_colors.append({
                'position': (x, y),
                'rgb': rgb_color,
                'hsv': tuple(hsv_color),
                'bgr': tuple(bgr_color)
            })
            
            self.analyze_colors()
    
    def analyze_colors(self):
        """Analyze all clicked colors and suggest HSV range"""
        if len(self.clicked_colors) < 1:
            return
            
        print(f"\n📊 Analysis of {len(self.clicked_colors)} clicked colors:")
        
        # Extract HSV values
        hue_values = [color['hsv'][0] for color in self.clicked_colors]
        sat_values = [color['hsv'][1] for color in self.clicked_colors]
        val_values = [color['hsv'][2] for color in self.clicked_colors]
        
        # Calculate ranges
        hue_min, hue_max = min(hue_values), max(hue_values)
        sat_min, sat_max = min(sat_values), max(sat_values)
        val_min, val_max = min(val_values), max(val_values)
        
        print(f"Hue range: {hue_min} - {hue_max}")
        print(f"Saturation range: {sat_min} - {sat_max}")
        print(f"Value range: {val_min} - {val_max}")
        
        # Suggest expanded ranges with margin
        hue_margin = max(5, (hue_max - hue_min) // 4)
        sat_margin = max(20, (sat_max - sat_min) // 4)
        val_margin = max(20, (val_max - val_min) // 4)
        
        suggested_lower = (
            max(0, hue_min - hue_margin),
            max(0, sat_min - sat_margin),
            max(0, val_min - val_margin)
        )
        suggested_upper = (
            min(179, hue_max + hue_margin),
            min(255, sat_max + sat_margin),
            min(255, val_max + val_margin)
        )
        
        print(f"\n💡 Suggested HSV range:")
        print(f"Lower: np.array([{suggested_lower[0]}, {suggested_lower[1]}, {suggested_lower[2]}])")
        print(f"Upper: np.array([{suggested_upper[0]}, {suggested_upper[1]}, {suggested_upper[2]}])")
        
        # Test the suggested range
        self.test_range(suggested_lower, suggested_upper)
    
    def test_range(self, lower, upper):
        """Test how many pixels the suggested range captures"""
        if self.hsv is None:
            return
            
        mask = cv2.inRange(self.hsv, np.array(lower), np.array(upper))
        pixel_count = cv2.countNonZero(mask)
        total_pixels = self.hsv.shape[0] * self.hsv.shape[1]
        percentage = (pixel_count / total_pixels) * 100
        
        print(f"🧪 Test results: {pixel_count} pixels ({percentage:.2f}% of screen)")
        
        # Find contours to see detected regions
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large_contours = [c for c in contours if cv2.contourArea(c) >= 50]
        
        print(f"🔍 Found {len(large_contours)} regions with area >= 50 pixels")
        
        if large_contours:
            print("Top regions:")
            for i, contour in enumerate(sorted(large_contours, key=cv2.contourArea, reverse=True)[:5]):
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                center_x, center_y = x + w//2, y + h//2
                print(f"  {i+1}. Center: ({center_x}, {center_y}), Area: {int(area)} pixels")
    
    def run(self):
        """Run the calibration tool"""
        print("🎨 Tree Indicator Color Calibrator")
        print("=" * 50)
        print("This tool helps you find the exact HSV color range for your tree indicators")
        print()
        print("Instructions:")
        print("1. Make sure RuneLite is visible with tree indicators showing")
        print("2. Press Enter to capture the screen")
        print("3. Click on different parts of the green tree indicators")
        print("4. The tool will analyze the colors and suggest HSV ranges")
        print("5. Press Ctrl+C to stop")
        print()
        
        input("Press Enter when ready to capture screen...")
        
        if not self.capture_screen():
            print("❌ Failed to capture screen")
            return
        
        print("✅ Screen captured!")
        print("👆 Now click on the GREEN tree indicators to analyze their colors")
        print("   (The tool will analyze each click and suggest HSV ranges)")
        print()
        
        # Start mouse listener
        self.running = True
        with mouse.Listener(on_click=self.on_click) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\n🛑 Stopping calibration...")
                self.running = False

def main():
    calibrator = ColorCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main()

