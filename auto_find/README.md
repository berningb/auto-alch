# Text Detection for NPCs, Items, and Interface Elements

This directory contains text detection scripts that can find and interact with text on screen using OCR (Optical Character Recognition).

## Files

- **`text_utils.py`** - Core utilities with the `findtextonscreen()` function
- **`text_detector.py`** - Full-featured text detection script with advanced options
- **`example_usage.py`** - Examples showing how to use the text detection
- **`README.md`** - This documentation file

## Main Function: `findtextonscreen()`

The primary function for detecting and interacting with text on screen.

### Usage

```python
from text_utils import findtextonscreen

# Basic usage - find and click on text
result = findtextonscreen("Banker")

# Advanced usage with options
result = findtextonscreen(
    target_text="Attack", 
    click=True,                    # Whether to click (default: True)
    pause=True,                    # Whether to pause for 'p' key (default: True)  
    confidence_threshold=0.7,      # OCR confidence 0.0-1.0 (default: 0.5)
    case_sensitive=False           # Case sensitive search (default: False)
)
```

### Return Value

The function returns a dictionary with:
- `success` (bool) - Whether the operation succeeded
- `text_found` (str) - The actual text that was detected
- `position` (tuple) - (x, y) coordinates where text was found
- `confidence` (float) - OCR confidence level (0.0-1.0)
- `error` (str) - Error message if operation failed

### Examples

```python
# Find and click an NPC
result = findtextonscreen("Bob the Builder")
if result['success']:
    print(f"Clicked on {result['text_found']} at {result['position']}")

# Find an item without clicking
result = findtextonscreen("Adamant sword", click=False)

# Search with higher confidence requirement  
result = findtextonscreen("Bank", confidence_threshold=0.8)
```

## Prerequisites

### Required Python Packages

Install these packages with pip:

```bash
pip install opencv-python numpy pyautogui pytesseract pynput
```

### Tesseract OCR

You need to install Tesseract OCR:

**Windows:**
1. Download from: https://github.com/tesseract-ocr/tesseract
2. Install to default location (usually `C:\Program Files\Tesseract-OCR\`)
3. If installed elsewhere, update the path in `text_detector.py`

**Linux:**
```bash
sudo apt install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

## How It Works

1. **Pause System**: Like other scripts in this project, it waits for you to press 'p' to start
2. **Screen Capture**: Takes a screenshot of your current screen
3. **OCR Processing**: Uses Tesseract to detect all text on screen with positions
4. **Text Matching**: Finds text that matches your search (case-insensitive by default)
5. **Click Action**: Moves mouse to text location and clicks (with small random offset)

## Running the Scripts

### Quick Test
```bash
python text_utils.py
```

### Full Test Suite
```bash
python text_detector.py
```

### Examples
```bash
python example_usage.py
```

## Use Cases

### NPC Interaction
```python
# Find and right-click an NPC
findtextonscreen("Shopkeeper")
```

### Item Management
```python
# Find item in inventory
result = findtextonscreen("Cooked fish", click=False)
if result['success']:
    print(f"Found fish at {result['position']}")
```

### Interface Navigation
```python
# Click interface buttons
findtextonscreen("Withdraw-All")
findtextonscreen("Close")
findtextonscreen("Accept")
```

### Combat/PvP
```python
# Find and target players/NPCs
findtextonscreen("Goblin")
findtextonscreen("Player123")
```

## Tips for Better Detection

1. **Use distinctive text** - Avoid common words like "the", "a", "and"
2. **Check confidence levels** - Use higher thresholds (0.7-0.9) for critical actions
3. **Use partial matches** - "withdraw" will match "Withdraw-All", "Withdraw-1", etc.
4. **Good lighting** - Make sure game interface is clearly visible
5. **Avoid overlapping windows** - Text detection works on whatever is visible

## Troubleshooting

### "Text not found"
- Make sure the text is clearly visible on screen
- Try lowering confidence_threshold (e.g., 0.3-0.5)
- Check if text might be partially obscured
- Use the scan mode to see what text is being detected

### "Failed to capture screen"
- Make sure the game window is visible
- Check that pyautogui has screen access permissions

### OCR accuracy issues
- Increase game UI scaling if text is too small
- Make sure there's good contrast between text and background
- Try different confidence thresholds

## Safety Features

- **Failsafe**: Move mouse to top-left corner to stop pyautogui
- **Pause system**: Must press 'p' to start actions (prevents accidental triggers)
- **Random offsets**: Clicks have small random variations to appear more natural
- **Error handling**: All functions return success/error status

## Integration with Other Scripts

The `findtextonscreen()` function can be easily integrated into other automation scripts:

```python
from auto_find.text_utils import findtextonscreen

# In your automation script
def bank_interaction():
    # Find and click banker
    if findtextonscreen("Banker")['success']:
        time.sleep(1)
        # Open bank interface
        if findtextonscreen("Bank")['success']:
            print("Successfully opened bank!")
```
