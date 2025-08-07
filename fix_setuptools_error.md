# Fix for setuptools.build_meta Error

## 🔧 Quick Fix

The error you're seeing is common with Python 3.13. Here's how to fix it:

### Step 1: Upgrade setuptools and pip

```bash
python -m pip install --upgrade pip setuptools wheel
```

### Step 2: Try installing packages again

```bash
# For the simple version (only needs Pillow)
python -m pip install Pillow

# For the full version
python -m pip install opencv-python pyautogui numpy
```

## 🛠️ Alternative Solutions

### If the above doesn't work, try:

```bash
# Install with --no-build-isolation flag
python -m pip install --no-build-isolation Pillow

# Or try with --user flag
python -m pip install --user Pillow

# Or try with trusted hosts
python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org Pillow
```

### If you still get errors:

```bash
# Install setuptools first
python -m pip install setuptools

# Then install Pillow
python -m pip install Pillow
```

## 🚀 Quick Test

After fixing the setuptools issue, test with:

```bash
# Navigate to your watchers folder
cd "C:\Users\User\Desktop\rs stuff\watchers"

# Install Pillow
python -m pip install Pillow

# Run the simple screen watcher
python simple_screen_watcher.py
```

## 💡 Why This Happens

- Python 3.13 is very new and some packages haven't updated their build systems yet
- The `setuptools.build_meta` backend is missing or outdated
- Upgrading pip and setuptools usually fixes this

## 🎯 Expected Result

After fixing this, you should be able to:
1. Install Pillow successfully
2. Run `python simple_screen_watcher.py`
3. See the screen watcher start monitoring your screen
4. Get "I can see!" messages when you move windows or click around


