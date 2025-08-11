import cv2
import numpy as np

# The crab color is FF00FFFF (cyan/magenta)
# Let's convert this to HSV to get the correct ranges

# FF00FFFF in BGR format (OpenCV uses BGR)
bgr_color = np.array([[[255, 0, 255]]], dtype=np.uint8)  # B=255, G=0, R=255
hsv_color = cv2.cvtColor(bgr_color, cv2.COLOR_BGR2HSV)

print(f"BGR color: {bgr_color[0][0]}")
print(f"HSV color: {hsv_color[0][0]}")

# For color detection, we need ranges around this value
h, s, v = hsv_color[0][0]
print(f"\nHue: {h}, Saturation: {s}, Value: {v}")

# Calculate ranges for detection
hue_range = 10
sat_range = 50
val_range = 50

hsv_lower = np.array([max(0, h - hue_range), max(0, s - sat_range), max(0, v - val_range)])
hsv_upper = np.array([min(179, h + hue_range), min(255, s + sat_range), min(255, v + val_range)])

print(f"\nSuggested HSV ranges:")
print(f"Lower: {hsv_lower}")
print(f"Upper: {hsv_upper}")

# Also test with wider ranges
hue_range_wide = 20
sat_range_wide = 100
val_range_wide = 100

hsv_lower_wide = np.array([max(0, h - hue_range_wide), max(0, s - sat_range_wide), max(0, v - val_range_wide)])
hsv_upper_wide = np.array([min(179, h + hue_range_wide), min(255, s + sat_range_wide), min(255, v + val_range_wide)])

print(f"\nWider HSV ranges:")
print(f"Lower: {hsv_lower_wide}")
print(f"Upper: {hsv_upper_wide}")

