# Attack Damage Detector

A Python script that detects orange damage numbers on screen in RuneScape and logs them with timestamps.

## Features

- 🎯 **Real-time Detection**: Continuously monitors screen for orange damage numbers
- 🔢 **OCR Recognition**: Uses Tesseract OCR to read exact damage values
- 📝 **Logging**: Saves all detected damage to JSON file with timestamps
- ⌨️ **Hotkey Controls**: Easy pause/resume and configuration during runtime
- 🎛️ **Customizable Detection Area**: Set specific screen regions for detection

## Usage

### Basic Usage

```bash
python auto_actions/attack_detector.py
```

### Quick Test

```bash
python auto_actions/test_attack_detector.py
```

## Controls

| Key | Action |
|-----|--------|
| `p` | Pause/Resume detection |
| `q` | Quit the program |
| `d` | Toggle debug output |
| `c` | Set detection region around mouse cursor |
| `x` | Clear custom detection region |

## How It Works

1. **Screen Capture**: Continuously captures screenshots
2. **Color Filtering**: Uses HSV color ranges to detect orange damage text
3. **Shape Analysis**: Filters contours by size and aspect ratio to find number-like shapes
4. **OCR Processing**: Uses Tesseract to read the actual damage values
5. **Logging**: Saves results with timestamps and positions

## Output

The detector creates:
- **Console output**: Real-time damage detection with timestamps
- **JSON log file**: `auto_actions/data/damage_log.json` with detailed records

### Example Log Entry
```json
{
  "timestamp": "2024-01-15T14:30:25.123456",
  "damage": 2,
  "position": [640, 360],
  "confidence": 0.85
}
```

## Requirements

- Python 3.7+
- OpenCV (`cv2`)
- PyAutoGUI
- NumPy
- pynput
- pytesseract (for OCR)

## Tips

1. **Position Detection**: The orange "2" in your screenshot should be detected easily
2. **Custom Regions**: Use `c` key to set detection area around where damage appears
3. **Debug Mode**: Use `d` key to see detailed detection information
4. **Cooldown**: Duplicate detections are filtered out automatically (2-second cooldown)

## Troubleshooting

- **No OCR**: Install `pytesseract` for number recognition
- **Low Detection**: Adjust HSV ranges in the code if needed
- **Too Many False Positives**: Use custom detection region (`c` key)

