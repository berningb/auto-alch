# Basic AI-Inspired Screen Watcher

A simple program that watches your screen and responds when it detects visual input.

## Features

- 🔍 **Screen Monitoring**: Continuously captures and analyzes your screen
- 👁️ **Visual Detection**: Detects when screen content changes
- 📊 **Basic Analysis**: Analyzes brightness and visual complexity
- 🤖 **AI-Inspired Responses**: Responds with "I can see!" when detecting visual input

## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required packages:

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install opencv-python pyautogui numpy
```

## Usage

Run the screen watcher:

```bash
python screen_watcher.py
```

The program will:
- Start monitoring your screen
- Print "I can see!" when it detects visual changes
- Provide additional analysis about screen brightness and complexity
- Continue running until you press `Ctrl+C` to stop

## How It Works

1. **Screen Capture**: Uses `pyautogui` to capture screenshots
2. **Change Detection**: Compares current frame with previous frame to detect changes
3. **Content Analysis**: Uses OpenCV to analyze:
   - Edge density (visual complexity)
   - Brightness levels
   - Overall screen content
4. **AI Response**: Responds when significant visual changes are detected

## Example Output

```
🤖 Basic AI-Inspired Screen Watcher
========================================
🔍 Starting screen watcher...
I'm watching your screen! Press Ctrl+C to stop.
[14:30:15] 👁️  I can see! Screen content detected!
   📊 High visual complexity detected
   💡 Bright screen detected
[14:30:20] 👁️  I can see! Screen content detected!
   🌙 Dark screen detected
```

## Customization

You can modify the detection sensitivity by changing the `threshold` parameter in the `detect_change` method. Lower values make it more sensitive to small changes.

## Requirements

- Python 3.7+
- Windows, macOS, or Linux
- Display with screen capture capability

## Notes

- The program runs continuously and may use some CPU resources
- It's designed to be a basic demonstration of AI-inspired screen monitoring
- Press `Ctrl+C` to stop the program at any time



