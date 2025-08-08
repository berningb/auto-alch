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
        self.quick_prayer_template = None
        self.config_path = os.path.join(self.current_dir, "config.json")
        self.qp_center = None  # (x, y) absolute screen coords
        self.qp_radius = None  # float
        self.qp_last_point = None  # last in-orb click point for micro-movement continuity
        self.qp_anchor_point = None  # slowly drifting "norm" point within orb
        
        # Load templates on initialization
        self.load_templates()
        # Load any saved calibration
        self._load_config()
    
    def load_templates(self):
        """Load template images for detection"""
        try:
            # Load stats template (try multiple common locations)
            candidate_stats_paths = [
                os.path.join(self.current_dir, "images", "stats.png"),
                os.path.join(self.current_dir, "skills", "images", "stats.png"),
                os.path.join(self.current_dir, "skills", "images", "stats_full.png"),
            ]
            self.stats_template = None
            for candidate in candidate_stats_paths:
                if os.path.exists(candidate):
                    self.stats_template = cv2.imread(candidate)
                    if self.stats_template is not None:
                        print(f"✅ Loaded stats template from {candidate}")
                        break
            if self.stats_template is None:
                print("ℹ️ No stats template found (optional). Skipping stats page verification.")
            
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
            
            # Load quick-prayer template if present
            qp_candidates = [
                os.path.join(self.current_dir, "images", "quick_prayer.png"),
                os.path.join(self.current_dir, "skills", "images", "quick_prayer.png"),
            ]
            for qp in qp_candidates:
                if os.path.exists(qp):
                    self.quick_prayer_template = cv2.imread(qp)
                    if self.quick_prayer_template is not None:
                        print(f"✅ Loaded quick-prayer template from {qp}")
                        break
            if self.quick_prayer_template is None:
                print("ℹ️ Quick-prayer template not found (mouse flick optional)")
                
        except Exception as e:
            print(f"Error loading templates: {e}")
    
    # --- Rapid input helpers for precise timing actions (e.g., prayer flick) ---
    def rapid_press(self, key: str, hold_seconds: float = 0.0):
        """Press a key with minimal global delay, optionally holding briefly.
        Respects a local timing without the module-wide pyautogui.PAUSE.
        """
        try:
            original_pause = pyautogui.PAUSE
            pyautogui.PAUSE = 0  # ensure immediate
            if hold_seconds and hold_seconds > 0:
                pyautogui.keyDown(key)
                time.sleep(hold_seconds)
                pyautogui.keyUp(key)
            else:
                pyautogui.press(key)
        finally:
            # restore global pause setting
            try:
                pyautogui.PAUSE = original_pause
            except Exception:
                pass

    # --- Quick-prayer calibration storage ---
    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                import json
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                qp = data.get("quick_prayer", {})
                if "center" in qp and isinstance(qp["center"], list) and len(qp["center"]) == 2:
                    self.qp_center = (int(qp["center"][0]), int(qp["center"][1]))
                if "radius" in qp:
                    self.qp_radius = float(qp["radius"])
                if self.qp_center:
                    print(f"🗺️ Loaded Quick-prayer calibration: center={self.qp_center}, radius={self.qp_radius}")
        except Exception as e:
            print(f"⚠️ Failed to load config: {e}")

    def _save_config(self):
        try:
            import json
            data = {}
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data.setdefault("quick_prayer", {})
            if self.qp_center:
                data["quick_prayer"]["center"] = [int(self.qp_center[0]), int(self.qp_center[1])]
            if self.qp_radius:
                data["quick_prayer"]["radius"] = float(self.qp_radius)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("💾 Saved Quick-prayer calibration.")
        except Exception as e:
            print(f"⚠️ Failed to save config: {e}")

    def set_quick_prayer_center(self, x: int, y: int):
        self.qp_center = (int(x), int(y))
        print(f"📍 Set Quick-prayer center to {self.qp_center}")
        self._save_config()

    def set_quick_prayer_edge(self, x: int, y: int):
        if self.qp_center is None:
            print("⚠️ Set center first (hotkey) before edge to compute radius.")
            return
        dx = int(x) - self.qp_center[0]
        dy = int(y) - self.qp_center[1]
        self.qp_radius = max(4.0, (dx * dx + dy * dy) ** 0.5)
        print(f"📏 Computed Quick-prayer radius ≈ {self.qp_radius:.1f} pixels")
        self._save_config()

    def get_quick_prayer_click_point(self):
        if not self.qp_center:
            return None
        cx, cy = self.qp_center
        # Click slightly within the radius; if radius unknown, small jitter
        r = self.qp_radius if self.qp_radius else 10.0
        r = max(6.0, min(r - 3.0, 20.0))
        angle = random.uniform(0, 2 * np.pi)
        # Use sqrt for uniform area distribution within circle
        dist = r * (random.random() ** 0.5)
        jitter_x = int(dist * np.cos(angle))
        jitter_y = int(dist * np.sin(angle))
        return (cx + jitter_x, cy + jitter_y)

    def random_point_in_orb(self, center=None, radius=None):
        base_center = center if center is not None else self.qp_center
        base_radius = radius if radius is not None else self.qp_radius
        if base_center is None:
            return None
        cx, cy = base_center
        r = base_radius if base_radius else 10.0
        r = max(6.0, min(r - 3.0, 20.0))
        angle = random.uniform(0, 2 * np.pi)
        dist = r * (random.random() ** 0.5)
        return (int(cx + dist * np.cos(angle)), int(cy + dist * np.sin(angle)))

    def step_point_in_orb(self, prev_point=None, center=None, radius=None, min_step: int = 2, max_step: int = 6):
        """Take a small step from the previous point within the orb bounds for natural micro movement."""
        base_center = center if center is not None else self.qp_center
        base_radius = radius if radius is not None else self.qp_radius
        if base_center is None:
            return None
        cx, cy = base_center
        if prev_point is None:
            prev_point = (cx, cy)
        px, py = prev_point
        # Choose a small random step
        step = random.randint(min_step, max_step)
        angle = random.uniform(0, 2 * np.pi)
        nx = px + int(step * np.cos(angle))
        ny = py + int(step * np.sin(angle))
        # Clamp to orb interior (shrink by 3px margin)
        r = base_radius if base_radius else 10.0
        r_eff = max(6.0, r - 3.0)
        # If outside, project back onto circle
        dx = nx - cx
        dy = ny - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > r_eff:
            if dist == 0:
                nx, ny = cx, cy
            else:
                scale = r_eff / dist
                nx = int(cx + dx * scale)
                ny = int(cy + dy * scale)
        return (nx, ny)

    def next_micro_point(self, prev_point=None, center=None, radius=None):
        """Choose the next in-orb point using human profile: ~90% 1–3 px, ~10% 4–6 px steps."""
        # Primary small steps
        if random.random() < 0.9:
            return self.step_point_in_orb(prev_point=prev_point, center=center, radius=radius, min_step=1, max_step=3)
        # Occasional slightly larger correction
        return self.step_point_in_orb(prev_point=prev_point, center=center, radius=radius, min_step=4, max_step=6)

    # --- Humanized quick movement for near-instant but realistic motion ---
    def human_quick_move(self, target_x: int, target_y: int):
        try:
            start_x, start_y = pyautogui.position()
            dx = target_x - start_x
            dy = target_y - start_y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance < 80:
                total_dur = random.uniform(0.10, 0.16)
            elif distance < 240:
                total_dur = random.uniform(0.16, 0.26)
            else:
                total_dur = random.uniform(0.22, 0.34)

            # Waypoint at 40–70% with small offset for curvature
            wp_frac = random.uniform(0.4, 0.7)
            wp_x = start_x + dx * wp_frac + random.randint(-3, 3)
            wp_y = start_y + dy * wp_frac + random.randint(-3, 3)

            pyautogui.moveTo(wp_x, wp_y, duration=total_dur * 0.55)
            pyautogui.moveTo(target_x, target_y, duration=total_dur * 0.45)
        except Exception as e:
            print(f"⚠️ human_quick_move failed: {e}")

    def human_micro_move(self, target_x: int, target_y: int):
        """Very small motion for within-orb adjustments; fast but not teleporting."""
        try:
            start_x, start_y = pyautogui.position()
            dx = target_x - start_x
            dy = target_y - start_y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 1:
                return
            duration = random.uniform(0.015, 0.05)
            pyautogui.moveTo(target_x, target_y, duration=duration)
        except Exception as e:
            print(f"⚠️ human_micro_move failed: {e}")

    def human_click_hold(self, x: int, y: int, hold_ms: int = 35):
        try:
            pyautogui.mouseDown(x=x, y=y, button='left')
            time.sleep(max(0.02, hold_ms / 1000.0))
            pyautogui.mouseUp(x=x, y=y, button='left')
        except Exception as e:
            print(f"⚠️ human_click_hold failed: {e}")

    def pray_tick(
        self,
        quick_prayer_key: str = 'f1',
        min_gap_ms: int = 40,
        max_gap_ms: int = 90,
        use_mouse: bool = True,
        settle_ms_min: int = 60,
        settle_ms_max: int = 110,
        hold_on_ms_min: int = 60,
        hold_on_ms_max: int = 100,
        hold_off_ms_min: int = 60,
        hold_off_ms_max: int = 100,
    ):
        """Perform a quick-prayer flick (toggle on then off rapidly).

        Args:
            quick_prayer_key: Hotkey bound to Quick-prayers toggle (used if use_mouse=False).
            min_gap_ms: Minimum gap between ON and OFF in milliseconds.
            max_gap_ms: Maximum gap between ON and OFF in milliseconds.
            use_mouse: If True, click the quick-prayer icon on the HUD via color; fallback to template if present.
        """
        try:
            gap = random.uniform(min_gap_ms / 1000.0, max_gap_ms / 1000.0)
            settle = random.uniform(max(0.0, settle_ms_min) / 1000.0, max(settle_ms_min, settle_ms_max) / 1000.0)
            hold_on = random.randint(max(1, hold_on_ms_min), max(hold_on_ms_min, hold_on_ms_max))
            hold_off = random.randint(max(1, hold_off_ms_min), max(hold_off_ms_min, hold_off_ms_max))
            if use_mouse:
                screen = self.capture_screen()
                if screen is None:
                    return False
                # Prefer calibrated location; start from last/anchor for continuity
                pos_center = self.qp_center
                pos_radius = self.qp_radius
                base = self.qp_last_point or self.qp_anchor_point
                if base is None and pos_center is not None:
                    # Initialize anchor near center
                    self.qp_anchor_point = self.random_point_in_orb(center=pos_center, radius=pos_radius)
                    base = self.qp_anchor_point
                # Small step from base; if no base, fall back to a random in-orb point
                if base is not None:
                    pos = self.next_micro_point(prev_point=base, center=pos_center, radius=pos_radius)
                else:
                    pos = self.random_point_in_orb(center=pos_center, radius=pos_radius)
                if pos is None:
                    # Color-based locate first
                    try:
                        detected_center = self.find_quick_prayer_orb(screen)
                        pos = detected_center
                    except Exception:
                        pos = None
                # Fallback to template center
                if pos is None and self.quick_prayer_template is not None:
                    qp_pos, qp_conf = self.find_template(screen, self.quick_prayer_template, threshold=0.65)
                    if qp_pos:
                        # Small jitter around template center
                        cx, cy = qp_pos
                        pos = (cx + random.randint(-4, 4), cy + random.randint(-4, 4))
                if pos is None:
                    print("⚠️ Quick-prayer icon not located")
                    return False
                original_pause = pyautogui.PAUSE
                pyautogui.PAUSE = 0
                # Quick but realistic movement; micro if close
                cur_x, cur_y = pyautogui.position()
                if ((pos[0]-cur_x)**2 + (pos[1]-cur_y)**2) ** 0.5 <= 12:
                    self.human_micro_move(pos[0], pos[1])
                else:
                    self.human_quick_move(pos[0], pos[1])
                # Brief settle before click for reliability
                time.sleep(settle)
                # Click ON with a short hold
                self.human_click_hold(pos[0], pos[1], hold_ms=hold_on)
                # Gap between toggles
                time.sleep(gap)
                # Slightly different nearby point within the orb for OFF (micro step)
                if pos_center is not None:
                    pos2 = self.next_micro_point(prev_point=pos, center=pos_center, radius=pos_radius)
                else:
                    pos2 = (pos[0] + random.randint(-2, 2), pos[1] + random.randint(-2, 2))
                # Minimal micro-move to emulate human adjustment
                self.human_micro_move(pos2[0], pos2[1])
                # Click OFF with a short hold
                self.human_click_hold(pos2[0], pos2[1], hold_ms=hold_off)
                pyautogui.PAUSE = original_pause
                # Remember last point for next invocation to avoid big jumps
                self.qp_last_point = pos2
                # Occasionally drift anchor slightly to a new local "norm" point
                if pos_center is not None and random.random() < 0.03:
                    self.qp_anchor_point = self.next_micro_point(prev_point=self.qp_anchor_point or pos2, center=pos_center, radius=pos_radius)
            else:
                # Keyboard fallback
                self.rapid_press(quick_prayer_key)
                time.sleep(gap)
                self.rapid_press(quick_prayer_key)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ✝️ Prayer flick (gap {int(gap*1000)} ms)")
            return True
        except Exception as e:
            print(f"❌ pray_tick failed: {e}")
            return False
    
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
    
    def checkstats(self, leveling_skill, method=None, interactive=True):
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
            
            # Optional interactive pause gate (skipped when called from automation loops)
            if interactive:
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


def checkstats(leveling_skill, method=None, interactive=True):
    """
    Convenience function to check stats without creating class instance
    
    Args:
        leveling_skill (str): The skill to check
        method (str, optional): Method to open stats - 'keybind', 'tab', or None for random choice
    
    Returns:
        bool: True if successful, False otherwise
    """
    functions = get_auto_functions()
    return functions.checkstats(leveling_skill, method, interactive=interactive)


def pray_tick(quick_prayer_key: str = 'f1', min_gap_ms: int = 40, max_gap_ms: int = 90):
    """Convenience wrapper to perform a single prayer flick."""
    functions = get_auto_functions()
    return functions.pray_tick(quick_prayer_key=quick_prayer_key, min_gap_ms=min_gap_ms, max_gap_ms=max_gap_ms)


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
