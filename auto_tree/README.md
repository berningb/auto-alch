# Tree Detector & Auto-Clicker

Automatically detects and clicks on trees highlighted by **Fiish's Tree Indicator** RuneLite plugin.

## Prerequisites

1. **RuneLite** with **Fiish's Tree Indicator plugin** installed and enabled
2. **Python 3.x** with required packages:
   ```bash
   pip install opencv-python pyautogui numpy pynput
   ```
3. Trees must be visible on your screen
4. Tree Indicator plugin should use the default green color: RGB(0, 200, 120)

## How It Works

The script uses computer vision to detect the green tree indicator overlays from your RuneLite plugin:

1. **Color Detection**: Looks for the specific green color used by the Tree Indicator plugin
2. **Shape Analysis**: Filters detected regions by size to avoid false positives
3. **Smart Targeting**: Prioritizes larger/more prominent tree indicators
4. **Natural Clicking**: Adds random offsets to make clicks appear more human-like

## Usage

Run the script:
```bash
python tree_detector.py
```

### Menu Options

1. **Detect and click best tree (once)** - Finds and clicks on the most prominent tree
2. **Test detection only (no clicking)** - Shows what trees are detected without clicking
3. **Continuous tree clicking** - Automatically clicks trees in a loop
4. **Exit** - Quit the program

### Controls

- Press **'p'** to start detection/clicking when prompted
- Press **Ctrl+C** to stop continuous mode

## Configuration

### Tree Indicator Plugin Settings

For best results, configure your Tree Indicator plugin:

- **Enable**: ✅ Tree Indicator enabled
- **Color**: Default green (RGB 0, 200, 120) 
- **Mode**: Either "Tile" or "Full Tree" works
- **Stroke Width**: 2-3 pixels recommended
- **Fill**: Optional (both filled and outline-only work)

### Script Settings

You can modify these values in the script if needed:

```python
# Color detection range (HSV)
lower_green = np.array([140, 180, 150])  # Lower bound
upper_green = np.array([170, 255, 255])  # Upper bound

# Minimum area for valid tree detection
min_area = 50  # pixels

# Click offset range
offset_x = random.randint(-10, 10)
offset_y = random.randint(-8, 8)
```

## Tree Types Supported

Works with any tree type that the Tree Indicator plugin highlights:

- 🌳 Regular trees
- 🌲 Oak, Willow, Maple trees  
- 🌴 Yew, Magic trees
- 🎋 Teak, Mahogany trees
- 🌿 And more (depends on plugin config)

## Troubleshooting

### "No tree indicators found"

1. Verify Tree Indicator plugin is **enabled**
2. Make sure **trees are visible** on screen
3. Check that trees are actually **highlighted** with green overlays
4. Ensure you're using the **default green color**

### Detection but no clicking

1. Check if click coordinates are within screen bounds
2. Verify game window is **active** and **focused**
3. Try adjusting the random offset range

### False positives

1. Increase `min_area` value to filter out small green elements
2. Adjust HSV color range to be more specific
3. Use "Test detection only" mode to see what's being detected

## Safety Features

- **Pause control**: Must press 'p' to start each action
- **Random delays**: 2-4 second delays in continuous mode
- **Random offsets**: Clicks are slightly randomized
- **Easy stopping**: Ctrl+C to stop at any time

## Example Output

```
🌳 Tree Detector & Auto-Clicker
==================================================
✅ Screen captured, analyzing for tree indicators...
🔍 Found 3 tree indicator regions
✅ Found 2 valid tree indicators:
   1. Position: (450, 320), Area: 156 pixels
   2. Position: (520, 280), Area: 98 pixels

🎯 Targeting best tree at (450, 320)
🖱️  Clicking tree at (445, 325)
   Original center: (450, 320)
   Random offset: (-5, 5)
✅ Successfully clicked on tree!
```

## Related Files

- `../auto_find/color_detection.py` - Color detection utilities
- `../auto_alch/` - Similar detection patterns for alchemy
- `../../fiish-runlite-plugins/fiish-tree-indicator/` - The RuneLite plugin source

