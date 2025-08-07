# Python Setup Guide for Windows

## 🐍 Step 1: Install Python

### Option A: Download from Python.org (Recommended)

1. **Go to Python Downloads:**
   - Visit: https://www.python.org/downloads/
   - Click the big yellow "Download Python" button

2. **Run the Installer:**
   - **IMPORTANT**: Check the box "Add Python to PATH" ✅
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   - Open a new Command Prompt or PowerShell
   - Type: `python --version`
   - You should see something like "Python 3.11.0"

### Option B: Microsoft Store (Alternative)

1. Open Microsoft Store
2. Search for "Python"
3. Install "Python 3.11" or latest version
4. This automatically adds Python to PATH

## 🔧 Step 2: Install Required Packages

Once Python is installed, open Command Prompt and run:

```bash
# Navigate to your watchers folder
cd "C:\Users\User\Desktop\rs stuff\watchers"

# Install Pillow for the simple version
python -m pip install Pillow

# Or install all packages for the full version
python -m pip install opencv-python pyautogui numpy
```

## 🚀 Step 3: Run the Screen Watcher

### Try the Simple Version First:
```bash
python simple_screen_watcher.py
```

### Or the Full Version:
```bash
python screen_watcher.py
```

## 🛠️ Troubleshooting

### If "python" command doesn't work:
- Try: `py --version`
- Or: `python3 --version`

### If you get permission errors:
- Run Command Prompt as Administrator
- Or use: `python -m pip install --user Pillow`

### If you get SSL errors:
- Try: `python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org Pillow`

## 📋 Quick Test Commands

After installing Python, test with these commands:

```bash
# Test Python installation
python --version

# Test pip installation
python -m pip --version

# Install Pillow
python -m pip install Pillow

# Run the simple screen watcher
python simple_screen_watcher.py
```

## 🎯 What to Expect

When you run the screen watcher:
1. It will start monitoring your screen
2. When you move windows, click, or change applications, it will say "I can see!"
3. Press `Ctrl+C` to stop the program

## 💡 Tips

- Make sure to check "Add Python to PATH" during installation
- Restart Command Prompt after installing Python
- The simple version only needs Pillow, which is easier to install
- If one method doesn't work, try the other installation options



