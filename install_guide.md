# Installation Guide for Windows

## Option 1: Using Python's built-in pip (Recommended)

If you have Python installed, try these commands:

```bash
python -m pip install -r requirements.txt
```

Or:
```bash
py -m pip install -r requirements.txt
```

## Option 2: Check if Python is installed

First, check if Python is installed:
```bash
python --version
```

If that doesn't work, try:
```bash
py --version
```

## Option 3: Install Python if not installed

If Python is not installed:

1. Go to https://www.python.org/downloads/
2. Download the latest Python version for Windows
3. **Important**: During installation, check "Add Python to PATH"
4. Restart your command prompt/PowerShell
5. Try the installation commands again

## Option 4: Using conda (if you have Anaconda/Miniconda)

```bash
conda install opencv pyautogui numpy
```

## Option 5: Manual installation

If the above doesn't work, install packages one by one:

```bash
python -m pip install opencv-python
python -m pip install pyautogui
python -m pip install numpy
```

## Troubleshooting

### If you get "pip is not recognized":
- Make sure Python is installed and added to PATH
- Try using `python -m pip` instead of just `pip`
- Restart your command prompt after installing Python

### If you get permission errors:
- Run command prompt as Administrator
- Or use: `python -m pip install --user -r requirements.txt`

### If you get SSL errors:
- Try: `python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt`

## Running the Program

Once packages are installed, run:
```bash
python screen_watcher.py
```

Or:
```bash
py screen_watcher.py
```



