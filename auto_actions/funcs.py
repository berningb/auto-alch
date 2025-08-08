#!/usr/bin/env python3
"""
Auto Actions Functions Module
Reusable functions for RuneScape automation scripts
"""

import cv2
import numpy as np
import pyautogui
import time
import random
import os
from datetime import datetime

# Configure pyautogui for safety
pyautogui.FAILSAFE = True  # Move mouse to corner to stop
pyautogui.PAUSE = 0.1  # Small pause between actions


class AutoActionFunctions:
    def __init__(self):
        self.stats_template = None
        self.skill_templates = {}  # Dictionary to store skill templates
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load templates on initialization
        self.load_templates()
    
    def load_templates(self):
        """Load template images for detection"""
        try:
            # Load stats template
            stats_path = os.path.join(self.current_dir, "images", "stats.png")
            
            if os.path.exists(stats_path):
                self.stats_template = cv2.imread(stats_path)
                print(f"✅ Loaded stats template from {stats_path}")
            else:
                print(f"❌ Stats template not found at {stats_path}")
            
            # Load skill templates
            skills_dir = os.path.join(self.current_dir, "skills", "images")
            if os.path.exists(skills_dir):
                skill_files = [f for f in os.listdir(skills_dir) if f.endswith('.png') and f != 'skills_tab.png' and f != 'stats_full.png']
                
                for skill_file in skill_files:
                    skill_name = skill_file.replace('.png', '').lower()
                    skill_path = os.path.join(skills_dir, skill_file)
                    
                    skill_template = cv2.imread(skill_path)
                    if skill_template is not None:
                        self.skill_templates[skill_name] = skill_template
                        print(f"✅ Loaded {skill_name} skill template")
                    else:
                        print(f"❌ Failed to load {skill_name} template")
                
                print(f"📊 Loaded {len(self.skill_templates)} skill templates")
            else:
                print(f"❌ Skills directory not found at {skills_dir}")
                print("📝 Please create skill template images in skills/images/ directory")
            
            # Load skills tab template
            skills_tab_path = os.path.join(self.current_dir, "skills", "images", "skills_tab.png")
            if os.path.exists(skills_tab_path):
                self.skills_tab_template = cv2.imread(skills_tab_path)
                print(f"✅ Loaded skills tab template")
            else:
                print(f"❌ Skills tab template not found at {skills_tab_path}")
                self.skills_tab_template = None
                
        except Exception as e:
            print(f"Error loading templates: {e}")
    
    def capture_screen(self):
        """Capture current screen"""
        try:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def find_template(self, screen, template, threshold=0.7):
        """Find template in screen using template matching"""
        try:
            if template is None:
                return None, 0
            
            # Convert to grayscale
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Template matching
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template_gray.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y), max_val
            else:
                return None, max_val
                
        except Exception as e:
            print(f"Error in template matching: {e}")
            return None, 0
    
    def add_click_variation(self, position):
        """Add random variation to click position for human-like behavior"""
        x, y = position
        
        # Natural variation - humans don't click the exact same spot
        base_variation = random.randint(3, 8)
        
        # Add realistic variation patterns
        if random.random() < 0.6:  # 60% chance for moderate variation
            variation_x = random.randint(-base_variation, base_variation)
            variation_y = random.randint(-base_variation, base_variation)
        elif random.random() < 0.3:  # 30% chance for more variation
            variation_x = random.randint(-base_variation-2, base_variation+2)
            variation_y = random.randint(-base_variation-2, base_variation+2)
        else:  # 10% chance for significant variation
            variation_x = random.randint(-base_variation-4, base_variation+4)
            variation_y = random.randint(-base_variation-4, base_variation+4)
        
        click_x = x + variation_x
        click_y = y + variation_y
        return (click_x, click_y)
    
    def human_click(self, position, action_name="Click"):
        """Click with human-like behavior"""
        try:
            varied_position = self.add_click_variation(position)
            x, y = varied_position
            
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Calculate distance for movement speed
            distance = ((x - current_x) ** 2 + (y - current_y) ** 2) ** 0.5
            
            # Natural human-like movement durations
            if distance < 50:
                movement_duration = random.uniform(0.08, 0.15)
            elif distance < 200:
                movement_duration = random.uniform(0.15, 0.3)
            else:
                movement_duration = random.uniform(0.25, 0.5)
            
            # Human-like movement with slight curve
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            
            # Move to target with waypoint for natural movement
            waypoint_x = current_x + (x - current_x) * random.uniform(0.3, 0.7)
            waypoint_y = current_y + (y - current_y) * random.uniform(0.3, 0.7)
            
            # Move through waypoint to target
            pyautogui.moveTo(waypoint_x + offset_x, waypoint_y + offset_y, duration=movement_duration * 0.6)
            pyautogui.moveTo(x, y, duration=movement_duration * 0.4)
            
            # Brief pause before clicking
            wait_time = random.uniform(0.02, 0.08)
            time.sleep(wait_time)
            
            pyautogui.click(x, y)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {action_name} at ({x}, {y})")
            
            return True
        except Exception as e:
            print(f"Error clicking: {e}")
            return False
    
    def press_key(self, key, description=""):
        """Press a key with human-like timing"""
        try:
            if description:
                print(f"   ⌨️ Pressing '{key}' to {description}...")
            else:
                print(f"   ⌨️ Pressing '{key}'...")
            time.sleep(random.uniform(0.1, 0.3))
            pyautogui.press(key)
            time.sleep(random.uniform(0.2, 0.5))
            return True
        except Exception as e:
            print(f"Error pressing key '{key}': {e}")
            return False
    
    def _click_skills_tab(self):
        """Helper method to click the skills tab"""
        try:
            # Load skills tab template if not already loaded
            if not hasattr(self, 'skills_tab_template') or self.skills_tab_template is None:
                skills_tab_path = os.path.join(self.current_dir, "skills", "images", "skills_tab.png")
                if os.path.exists(skills_tab_path):
                    self.skills_tab_template = cv2.imread(skills_tab_path)
                else:
                    print(f"❌ Skills tab template not found at {skills_tab_path}")
                    return False
            
            # Capture screen and find skills tab
            screen = self.capture_screen()
            if screen is None:
                print("❌ Could not capture screen for tab detection")
                return False
            
            # Find skills tab
            tab_position, tab_confidence = self.find_template(screen, self.skills_tab_template, threshold=0.6)
            
            if not tab_position or tab_confidence < 0.6:
                print(f"❌ Could not find skills tab (confidence: {tab_confidence:.2f})")
                return False
            
            print(f"🎯 Found skills tab at {tab_position} (confidence: {tab_confidence:.2f})")
            
            # Click skills tab with randomization
            template_height, template_width = self.skills_tab_template.shape[:2]
            center_x, center_y = tab_position
            half_width = template_width // 2
            half_height = template_height // 2
            
            # Random click position within tab
            random_x = random.randint(center_x - half_width + 5, center_x + half_width - 5)
            random_y = random.randint(center_y - half_height + 5, center_y + half_height - 5)
            random_position = (random_x, random_y)
            
            print(f"🖱️ Clicking skills tab at {random_position} (offset: {random_x - center_x:+d}, {random_y - center_y:+d})")
            
            return self.human_click(random_position, "🎯 Clicked skills tab")
            
        except Exception as e:
            print(f"❌ Error clicking skills tab: {e}")
            return False
    
    def find_skill_position(self, screen, leveling_skill):
        """
        Find the position of a specific skill on the stats page using template matching
        
        Args:
            screen: The captured screen image
            leveling_skill (str): The skill to find
            
        Returns:
            tuple: (x, y) position of the skill, or None if not found
        """
        skill_lower = leveling_skill.lower()
        
        # Check if we have a template for this skill
        if skill_lower not in self.skill_templates:
            print(f"❌ No template found for skill: {leveling_skill}")
            print(f"📝 Available skills: {list(self.skill_templates.keys())}")
            print(f"💡 Please create {skill_lower}.png in skills/images/ directory")
            return None
        
        # Find the skill using template matching
        skill_template = self.skill_templates[skill_lower]
        skill_position, confidence = self.find_template(screen, skill_template, threshold=0.6)
        
        if skill_position and confidence > 0.6:
            # Get template dimensions for random positioning
            template_height, template_width = skill_template.shape[:2]
            center_x, center_y = skill_position
            
            # Calculate the skill area bounds (template area around the center)
            half_width = template_width // 2
            half_height = template_height // 2
            
            # Pick a random point within the skill template area
            random_x = random.randint(center_x - half_width + 5, center_x + half_width - 5)
            random_y = random.randint(center_y - half_height + 5, center_y + half_height - 5)
            
            random_position = (random_x, random_y)
            
            print(f"🎯 Found {leveling_skill} skill at {skill_position} (confidence: {confidence:.2f})")
            print(f"🎲 Random hover point: {random_position} (offset: {random_x - center_x:+d}, {random_y - center_y:+d})")
            return random_position
        else:
            print(f"❌ Could not find {leveling_skill} skill on screen (best match: {confidence:.2f})")
            print(f"💡 Try taking a screenshot of just the {leveling_skill} skill icon and save as skills/images/{skill_lower}.png")
            return None
    
    def checkstats(self, leveling_skill, method=None):
        """
        Open stats page and hover over the specified leveling skill
        
        Args:
            leveling_skill (str): The skill to check (e.g., 'attack', 'magic', etc.)
            method (str, optional): Method to open stats - 'keybind', 'tab', or None for random choice
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Determine method to use
            if method is None:
                chosen_method = random.choice(['keybind', 'tab'])
                print(f"🎲 Randomly choosing method: {chosen_method}")
            elif method.lower() in ['keybind', 'key', '4']:
                chosen_method = 'keybind'
            elif method.lower() in ['tab', 'click']:
                chosen_method = 'tab'
            else:
                print(f"❌ Invalid method: {method}. Using random choice.")
                chosen_method = random.choice(['keybind', 'tab'])
            
            print(f"📊 Preparing to check stats for skill: {leveling_skill} using {chosen_method}")
            print("⏸️  PAUSED - Click into your game screen and press 'p' to start the test")
            
            # Start paused, wait for 'p' key
            is_paused = True
            
            # Import keyboard listener
            from pynput import keyboard
            
            def on_key_press(key):
                nonlocal is_paused
                try:
                    if key.char == 'p':
                        is_paused = False
                        print("▶️  UNPAUSED - Starting checkstats action...")
                        return False  # Stop listener
                except AttributeError:
                    pass
            
            # Start keyboard listener
            listener = keyboard.Listener(on_press=on_key_press)
            listener.start()
            
            # Wait for unpause
            while is_paused:
                time.sleep(0.1)
            
            listener.stop()
            
            # Step 1: Open stats using chosen method
            if chosen_method == 'keybind':
                print("⌨️ Using keybind method: Pressing '4' to switch to stats...")
                if not self.press_key('4', "switch to stats"):
                    return False
            else:  # tab method
                print("🖱️ Using tab method: Clicking skills tab to open stats...")
                if not self._click_skills_tab():
                    return False
            
            # Quick wait for stats page to load
            time.sleep(random.uniform(0.2, 0.4))
            
            # Step 2: Capture screen to check if stats page is open
            screen = self.capture_screen()
            if screen is None:
                print("❌ Could not capture screen")
                return False
            
            # Step 3: Check if stats.png template is visible (optional verification)
            if self.stats_template is not None:
                stats_position, stats_confidence = self.find_template(screen, self.stats_template, threshold=0.6)
                if stats_position and stats_confidence > 0.6:
                    print(f"✅ Stats page detected (confidence: {stats_confidence:.2f})")
                else:
                    print(f"⚠️ Stats page detection uncertain (confidence: {stats_confidence:.2f})")
            
            # Step 4: Find the position of the leveling skill
            skill_position = self.find_skill_position(screen, leveling_skill)
            if skill_position is None:
                return False
            
            # Step 5: Move mouse to hover over the skill
            print(f"🖱️ Moving mouse to hover over {leveling_skill}...")
            
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            target_x, target_y = skill_position
            
            # Calculate distance for movement speed
            distance = ((target_x - current_x) ** 2 + (target_y - current_y) ** 2) ** 0.5
            
            # Faster movement durations
            if distance < 100:
                movement_duration = random.uniform(0.1, 0.2)
            elif distance < 300:
                movement_duration = random.uniform(0.15, 0.3)
            else:
                movement_duration = random.uniform(0.2, 0.4)
            
            # Use the already randomized skill position
            target_x, target_y = skill_position
            
            # Move mouse with natural curve
            waypoint_x = current_x + (target_x - current_x) * random.uniform(0.3, 0.7)
            waypoint_y = current_y + (target_y - current_y) * random.uniform(0.3, 0.7)
            
            pyautogui.moveTo(waypoint_x, waypoint_y, duration=movement_duration * 0.6)
            pyautogui.moveTo(target_x, target_y, duration=movement_duration * 0.4)
            
            # Quick hover to see the skill tooltip
            hover_time = random.uniform(0.3, 0.6)
            print(f"⏳ Hovering over {leveling_skill} for {hover_time:.1f} seconds...")
            time.sleep(hover_time)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ✅ Successfully checked {leveling_skill} stats")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in checkstats: {e}")
            return False


# Convenience function for easy importing
def get_auto_functions():
    """Get an instance of AutoActionFunctions"""
    return AutoActionFunctions()


def checkstats(leveling_skill, method=None):
    """
    Convenience function to check stats without creating class instance
    
    Args:
        leveling_skill (str): The skill to check
        method (str, optional): Method to open stats - 'keybind', 'tab', or None for random choice
    
    Returns:
        bool: True if successful, False otherwise
    """
    functions = get_auto_functions()
    return functions.checkstats(leveling_skill, method)


if __name__ == "__main__":
    # Quick test when run directly
    print("🧪 Testing checkstats function...")
    print("Available skills: attack, strength, defence, ranged, prayer, magic, runecrafting, construction,")
    print("                 hitpoints, agility, herblore, thieving, crafting, fletching, slayer, hunter,")
    print("                 mining, smithing, fishing, cooking, firemaking, woodcutting, farming")
    
    # Test with magic skill
    test_skill = "magic"
    print(f"\n🎯 Testing with skill: {test_skill}")
    result = checkstats(test_skill)
    if result:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")
