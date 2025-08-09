#!/usr/bin/env python3
"""
Simple Auto Alch - Clicks alch spell then darts
"""

import cv2
import numpy as np
import pyautogui
import time
import random
import os
import threading
from datetime import datetime
from pynput import keyboard

# Configure pyautogui for safety
pyautogui.FAILSAFE = True  # Move mouse to corner to stop
pyautogui.PAUSE = 0.1  # Small pause between actions

class SimpleAutoAlch:
    def __init__(self):
        self.alch_spell_template = None
        self.alch_spell_template2 = None
        self.alch_spell_template3 = None
        self.alch_templates = []  # list[(np.ndarray, str)] for all alc-spell*.png
        self.dart_templates = []  # list[(np.ndarray, str)]
        self.click_count = 0
        self.is_running = False
        self.is_paused = True
        # Screenshot → screen scaling (for Retina/HiDPI)
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # Humanization settings
        self.session_start_time = time.time()
        self.last_break_time = time.time()
        self.break_interval = random.randint(600, 1200)  # 10-20 minutes
        self.break_duration = random.randint(30, 120)  # 30 seconds - 2 minutes
        
        # State tracking
        self.waiting_for_alch_spell = True
        self.waiting_for_darts = False
        
        # Recovery tracking
        self.dart_fail_count = 0
        self.max_dart_fails = 3  # After 3 failed attempts, try inventory recovery
        
        # Keyboard listener for pause functionality
        self.keyboard_listener = None
        
        # Color-based detection settings (blue darts)
        # HSV bounds tuned for bright blue items; adjust if needed
        self.blue_hsv_lower = np.array([100, 120, 120])
        self.blue_hsv_upper = np.array([130, 255, 255])
        # Area constraints to filter noise (in pixels)
        self.min_area_dart = 800.0
        self.max_area_dart = 150000.0
        # Reject regions touching image edges
        self.edge_margin = 2

        # Tab hotkeys (adjust to match your client settings)
        self.key_inventory = 'f4'    # Inventory tab
        self.key_equipment = '5'     # Worn equipment tab
        self.key_spellbook = '3'     # Spellbook tab

        # Flow control: ensure we only click darts right after alch
        self.alch_armed = False

        # Logging and metrics
        self.debug = False  # Concise logs by default
        self.messed_up_count = 0  # Times we had to recover (inventory/equipment)
        self.total_break_time = 0.0  # Seconds spent in breaks

        # Fast mode settings (speed up the loop: alch → darts → alch ...)
        self.fast_mode = True
        # Speed multipliers and timings
        if self.fast_mode:
            pyautogui.PAUSE = 0.05
            self.movement_speed_multiplier = 0.6
            self.click_pause_min, self.click_pause_max = 0.01, 0.03
            # Fallback wait if chain re-arm doesn't find the spell quickly
            self.post_dart_wait_min, self.post_dart_wait_max = 0.40, 0.70
            self.darts_hover_min, self.darts_hover_max = 0.00, 0.02
            # Chain re-arm settings (scan for alch immediately after darts)
            self.rearm_timeout_sec = 1.80
            self.rearm_poll_min, self.rearm_poll_max = 0.03, 0.06
            self.rearm_spell4_threshold = 0.85
        else:
            self.movement_speed_multiplier = 1.0
            self.click_pause_min, self.click_pause_max = 0.02, 0.08
            self.post_dart_wait_min, self.post_dart_wait_max = 2.0, 3.0
            self.darts_hover_min, self.darts_hover_max = 0.10, 0.20
            self.rearm_timeout_sec = 2.50
            self.rearm_poll_min, self.rearm_poll_max = 0.10, 0.20
            self.rearm_spell4_threshold = 0.90
        
        # Color-based detection settings (alch spell - orange/yellow hues)
        # Broad range for the High Alchemy icon; tune if needed
        self.alch_hsv_lower = np.array([5, 120, 120])
        self.alch_hsv_upper = np.array([35, 255, 255])
        self.min_area_alch = 600.0
        self.max_area_alch = 200000.0

    def load_templates(self):
        """Load the template images"""
        try:
            # Load alch spell templates
            self.alch_spell_template = None
            self.alch_spell_template2 = None
            self.alch_spell_template3 = None
            
            # Get absolute paths (prefer images/ subdirectory, fallback to current dir)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            images_dir = os.path.join(current_dir, "images")
            alch_path_candidates = [
                os.path.join(images_dir, "alc-spell.png"),
                os.path.join(current_dir, "alc-spell.png"),
            ]
            alch2_path_candidates = [
                os.path.join(images_dir, "alc-spell2.png"),
                os.path.join(current_dir, "alc-spell2.png"),
            ]
            alch3_path_candidates = [
                os.path.join(images_dir, "alc-spell3.png"),
                os.path.join(current_dir, "alc-spell3.png"),
            ]
            # Resolve first existing candidate
            alch_path = next((p for p in alch_path_candidates if os.path.exists(p)), alch_path_candidates[0])
            alch2_path = next((p for p in alch2_path_candidates if os.path.exists(p)), alch2_path_candidates[0])
            alch3_path = next((p for p in alch3_path_candidates if os.path.exists(p)), alch3_path_candidates[0])
            
            print(f"Looking for alch templates in: {current_dir}")
            print(f"Full path 1: {alch_path}")
            print(f"Full path 2: {alch2_path}")
            
            if os.path.exists(alch_path):
                self.alch_spell_template = cv2.imread(alch_path)
                print("✅ Loaded alch spell template 1 (alc-spell.png)")
            else:
                print(f"❌ Could not find {alch_path}")
            
            if os.path.exists(alch2_path):
                self.alch_spell_template2 = cv2.imread(alch2_path)
                print("✅ Loaded alch spell template 2 (alc-spell2.png)")
            else:
                print(f"❌ Could not find {alch2_path}")
            
            if os.path.exists(alch3_path):
                self.alch_spell_template3 = cv2.imread(alch3_path)
                print("✅ Loaded alch spell template 3 (alc-spell3.png)")
            else:
                print(f"❌ Could not find {alch3_path}")
            
            # Dynamically load ANY alc-spell*.png templates
            self.alch_templates = []
            alch_seen = set()
            for dir_path in [images_dir, current_dir]:
                if not os.path.isdir(dir_path):
                    continue
                for fname in sorted(os.listdir(dir_path)):
                    lower = fname.lower()
                    if not lower.startswith("alc-spell") or not lower.endswith(".png"):
                        continue
                    full_path = os.path.join(dir_path, fname)
                    if full_path in alch_seen or not os.path.exists(full_path):
                        continue
                    img = cv2.imread(full_path)
                    if img is not None:
                        self.alch_templates.append((img, fname))
                        alch_seen.add(full_path)
                        print(f"✅ Loaded alch template: {fname}")
            # Ensure legacy three are included in the list (avoid duplicates by label)
            legacy = [
                (self.alch_spell_template, "alc-spell.png"),
                (self.alch_spell_template2, "alc-spell2.png"),
                (self.alch_spell_template3, "alc-spell3.png"),
            ]
            existing_labels = {name for _img, name in self.alch_templates}
            for img, name in legacy:
                if img is not None and name not in existing_labels:
                    self.alch_templates.append((img, name))
                    print(f"✅ Added legacy alch template into list: {name}")
            if not self.alch_templates:
                print("❌ No alch spell templates found. Please add one or more alc-spell*.png files")
                return False
            
            # Load any dart*.png templates dynamically (supports new additions)
            self.dart_templates = []
            candidate_dirs = [images_dir, current_dir]
            seen = set()
            for dir_path in candidate_dirs:
                if not os.path.isdir(dir_path):
                    continue
                for fname in sorted(os.listdir(dir_path)):
                    lower = fname.lower()
                    if not lower.startswith("dart") or not lower.endswith(".png"):
                        continue
                    full_path = os.path.join(dir_path, fname)
                    # Avoid duplicates across dirs
                    if full_path in seen or not os.path.exists(full_path):
                        continue
                    img = cv2.imread(full_path)
                    if img is not None:
                        self.dart_templates.append((img, fname))
                        seen.add(full_path)
                        print(f"✅ Loaded dart template: {fname}")
            if not self.dart_templates:
                print("❌ No dart templates found. Please add one or more dart*.png files")
                return False
                
            return True
        except Exception as e:
            print(f"Error loading templates: {e}")
            return False
    
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
 
    def find_template_multiscale(self, screen, template, scales=None):
        """Find best match for a template across multiple scales.
        Returns (position_or_None, best_confidence)
        """
        try:
            if template is None:
                return None, 0.0
            if scales is None:
                scales = [0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15, 1.20]

            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            best_pos = None
            best_conf = 0.0

            for s in scales:
                try:
                    # Resize template; skip invalid sizes
                    h0, w0 = template.shape[:2]
                    new_w = max(2, int(round(w0 * s)))
                    new_h = max(2, int(round(h0 * s)))
                    if new_w < 2 or new_h < 2:
                        continue
                    resized = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA if s < 1.0 else cv2.INTER_CUBIC)
                    tmpl_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                    res = cv2.matchTemplate(screen_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    if max_val > best_conf:
                        th, tw = tmpl_gray.shape
                        best_conf = float(max_val)
                        best_pos = (max_loc[0] + tw // 2, max_loc[1] + th // 2)
                except Exception:
                    continue

            return best_pos, best_conf
        except Exception as e:
            print(f"Error in multiscale template matching: {e}")
            return None, 0.0
 
    def find_by_orb(self, screen, template):
        """Locate template using ORB keypoints + homography. Returns (pos, confidence).
        Confidence is inlier_ratio in [0,1]."""
        try:
            if template is None:
                return None, 0.0
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            tmpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            orb = cv2.ORB_create(nfeatures=1200)
            kp1, des1 = orb.detectAndCompute(tmpl_gray, None)
            kp2, des2 = orb.detectAndCompute(screen_gray, None)
            if des1 is None or des2 is None or len(kp1) < 8 or len(kp2) < 8:
                return None, 0.0
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(des1, des2, k=2)
            good = []
            for m_n in matches:
                if len(m_n) < 2:
                    continue
                m, n = m_n
                if m.distance < 0.75 * n.distance:
                    good.append(m)
            if len(good) < 8:
                return None, 0.0
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if H is None or mask is None:
                return None, 0.0
            inliers = int(mask.sum())
            inlier_ratio = float(inliers) / max(1, len(good))
            h, w = tmpl_gray.shape
            corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
            projected = cv2.perspectiveTransform(corners, H)
            cx = int(projected[:, 0, 0].mean())
            cy = int(projected[:, 0, 1].mean())
            return (cx, cy), float(inlier_ratio)
        except Exception:
            return None, 0.0

    def _spellbook_roi(self, screen_shape):
        """Heuristic ROI for spellbook panel on the right side of the client.
        Returns (x1, y1, x2, y2)."""
        h, w = screen_shape[:2]
        x1 = int(0.55 * w)
        x2 = max(x1 + 10, w - 8)
        y1 = int(0.25 * h)
        y2 = max(y1 + 10, int(0.95 * h))
        return x1, y1, x2, y2

    def find_alch_spell(self, screen):
        """Find alch spell using template-only multi-scale matching across all loaded templates."""
        templates = list(self.alch_templates or [])
        if not templates:
            # Fallback to legacy variables if list not populated for some reason
            if self.alch_spell_template is not None:
                templates.append((self.alch_spell_template, "alc-spell.png"))
            if self.alch_spell_template2 is not None:
                templates.append((self.alch_spell_template2, "alc-spell2.png"))
            if self.alch_spell_template3 is not None:
                templates.append((self.alch_spell_template3, "alc-spell3.png"))

        best_pos = None
        best_conf = 0.0
        best_label = None
        for tmpl, label in templates:
            pos, conf = self.find_template_multiscale(screen, tmpl)
            if conf > best_conf and pos is not None:
                best_pos = pos
                best_conf = conf
                best_label = label

        if self.debug and best_label:
            print(f"   🔮 Best alch match: {best_label} (conf {best_conf:.2f}) at {best_pos}")
        return best_pos, best_conf
    
    def find_darts(self, screen):
        """Find darts via color segmentation, confirming within ROI using templates.
        This avoids any hardcoded screen points and adapts to different displays.
        """
        color_pos, color_conf = self._find_darts_by_color(screen)
        if color_pos is not None:
            return color_pos, color_conf
        return None, 0.0

    def _find_darts_by_color(self, screen):
        """Detect blue-colored dart region and optionally confirm with templates.
        Returns: (position_tuple_or_None, confidence_float)
        """
        try:
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.blue_hsv_lower, self.blue_hsv_upper)
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None, 0.0

            # Pick the largest valid blue region
            h_img, w_img = screen.shape[:2]
            best_region = None
            best_area = 0.0
            for c in contours:
                area = float(cv2.contourArea(c))
                if area < self.min_area_dart or area > self.max_area_dart:
                    continue
                x, y, w, h = cv2.boundingRect(c)
                if x <= self.edge_margin or y <= self.edge_margin or (x + w) >= (w_img - self.edge_margin) or (y + h) >= (h_img - self.edge_margin):
                    continue
                if area > best_area:
                    best_area = area
                    best_region = (x, y, w, h)

            if best_region is None:
                return None, 0.0

            x, y, w, h = best_region
            cx, cy = x + w // 2, y + h // 2

            # Try to confirm within ROI using available templates
            roi_pad = 8
            x1 = max(0, x - roi_pad)
            y1 = max(0, y - roi_pad)
            x2 = min(w_img, x + w + roi_pad)
            y2 = min(h_img, y + h + roi_pad)
            roi = screen[y1:y2, x1:x2]

            best_pos = (cx, cy)
            best_conf = 0.7  # default confidence if only color is used

            template_candidates = self.dart_templates or []
            for tmpl, label in template_candidates:
                # Local template match within ROI
                try:
                    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
                    res = cv2.matchTemplate(roi_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    if max_val > best_conf:
                        th, tw = tmpl_gray.shape
                        abs_x = x1 + max_loc[0] + tw // 2
                        abs_y = y1 + max_loc[1] + th // 2
                        best_pos = (abs_x, abs_y)
                        best_conf = float(max_val)
                        if self.debug:
                            print(f"   🎯 Color-ROI confirmed with dart template {label} (confidence: {best_conf:.2f})")
                except Exception:
                    # If ROI matching fails, keep color-based result
                    pass

            if best_pos is not None:
                if self.debug:
                    print(f"   🎨 Blue region detected at {best_pos} (area: {int(best_area)})")
                return best_pos, best_conf

            return None, 0.0
        except Exception as e:
            print(f"   ❌ Error in color-based dart detection: {e}")
            return None, 0.0

    def _find_alch_by_color(self, screen):
        """Detect orange/yellow alch icon region with ROI template confirmation.
        Returns: (position_tuple_or_None, confidence_float)
        """
        try:
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.alch_hsv_lower, self.alch_hsv_upper)
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None, 0.0

            h_img, w_img = screen.shape[:2]
            best_region = None
            best_area = 0.0
            for c in contours:
                area = float(cv2.contourArea(c))
                if area < self.min_area_alch or area > self.max_area_alch:
                    continue
                x, y, w, h = cv2.boundingRect(c)
                if x <= self.edge_margin or y <= self.edge_margin or (x + w) >= (w_img - self.edge_margin) or (y + h) >= (h_img - self.edge_margin):
                    continue
                if area > best_area:
                    best_area = area
                    best_region = (x, y, w, h)

            if best_region is None:
                return None, 0.0

            x, y, w, h = best_region
            cx, cy = x + w // 2, y + h // 2

            roi_pad = 8
            x1 = max(0, x - roi_pad)
            y1 = max(0, y - roi_pad)
            x2 = min(w_img, x + w + roi_pad)
            y2 = min(h_img, y + h + roi_pad)
            roi = screen[y1:y2, x1:x2]

            best_pos = (cx, cy)
            best_conf = 0.7

            # Prepare available alch templates
            alch_templates = []
            if self.alch_spell_template is not None:
                alch_templates.append((self.alch_spell_template, "alc-spell.png"))
            if self.alch_spell_template2 is not None:
                alch_templates.append((self.alch_spell_template2, "alc-spell2.png"))
            if self.alch_spell_template3 is not None:
                alch_templates.append((self.alch_spell_template3, "alc-spell3.png"))

            for tmpl, label in alch_templates:
                try:
                    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
                    res = cv2.matchTemplate(roi_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    if max_val > best_conf:
                        th, tw = tmpl_gray.shape
                        abs_x = x1 + max_loc[0] + tw // 2
                        abs_y = y1 + max_loc[1] + th // 2
                        best_pos = (abs_x, abs_y)
                        best_conf = float(max_val)
                        if self.debug:
                            print(f"   🎯 Color-ROI confirmed with alch template {label} (confidence: {best_conf:.2f})")
                except Exception:
                    pass

            if best_pos is not None:
                if self.debug:
                    print(f"   🟡 Alch color region at {best_pos} (area: {int(best_area)})")
                return best_pos, best_conf

            return None, 0.0
        except Exception as e:
            print(f"   ❌ Error in color-based alch detection: {e}")
            return None, 0.0
    
    def add_click_variation(self, position, base_range: tuple | None = None):
        """Add random variation to click position"""
        x, y = position
        
        # Choose base variation window
        if base_range is None:
            base_min, base_max = 3, 8
        else:
            base_min, base_max = base_range
        base_variation = random.randint(base_min, base_max)
        
        # Add more realistic variation patterns
        roll = random.random()
        if roll < 0.6:  # 60% chance for moderate variation
            variation_x = random.randint(-base_variation, base_variation)
            variation_y = random.randint(-base_variation, base_variation)
        elif roll < 0.9:  # 30% chance for more variation
            variation_x = random.randint(-base_variation-3, base_variation+3)
            variation_y = random.randint(-base_variation-3, base_variation+3)
        else:  # 10% chance for significant variation
            variation_x = random.randint(-base_variation-6, base_variation+6)
            variation_y = random.randint(-base_variation-6, base_variation+6)
        
        click_x = x + variation_x
        click_y = y + variation_y
        return (click_x, click_y)
    
    def human_click(self, position, action_name):
        """Click with human-like behavior"""
        try:
            # Increase variation specifically for alch/darts to avoid repeat pixels
            lower_name = (action_name or "").lower()
            if "alch" in lower_name:
                # Minimal variation for precision during debugging
                varied_position = self.add_click_variation(position, base_range=(0, 2))
            elif "darts" in lower_name:
                varied_position = self.add_click_variation(position, base_range=(5, 12))
            else:
                varied_position = self.add_click_variation(position)
            # Convert to screen coordinates considering Retina scaling
            x, y = self._to_screen_coords(varied_position)
            # Clamp within screen bounds
            try:
                sw, sh = pyautogui.size()
                x = max(2, min(int(x), sw - 3))
                y = max(2, min(int(y), sh - 3))
            except Exception:
                pass
            
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Calculate distance for movement speed
            distance = ((x - current_x) ** 2 + (y - current_y) ** 2) ** 0.5
            
            # Natural human-like movement durations
            if distance < 50:
                movement_duration = random.uniform(0.08, 0.15)
            elif distance < 200:
                movement_duration = random.uniform(0.15, 0.30)
            else:
                movement_duration = random.uniform(0.25, 0.50)
            # Apply fast-mode multiplier
            movement_duration *= getattr(self, "movement_speed_multiplier", 1.0)
            
            # Human-like movement with slight curve
            # Add a small random offset for natural variation
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            
            # Move to target with slight curve (more natural)
            # Add a waypoint for more human-like movement
            waypoint_x = current_x + (x - current_x) * random.uniform(0.3, 0.7)
            waypoint_y = current_y + (y - current_y) * random.uniform(0.3, 0.7)
            
            # Move through waypoint to target
            pyautogui.moveTo(waypoint_x + offset_x, waypoint_y + offset_y, duration=movement_duration * 0.6)
            pyautogui.moveTo(x, y, duration=movement_duration * 0.4)
            
            # Brief pause before clicking (much shorter)
            wait_time = random.uniform(self.click_pause_min, self.click_pause_max)
            time.sleep(wait_time)
            
            pyautogui.click(x, y)
            
            if self.debug:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {action_name} at OS({x}, {y}) from img{varied_position}")
            
            return True
        except Exception as e:
            print(f"Error clicking: {e}")
            return False
    
    def press_key(self, key, description=""):
        """Press a key with human-like timing"""
        try:
            if self.debug:
                if description:
                    print(f"   ⌨️ Pressing '{key}' to {description}...")
                else:
                    print(f"   ⌨️ Pressing '{key}'...")
            if self.fast_mode:
                time.sleep(random.uniform(0.05, 0.12))
            else:
                time.sleep(random.uniform(0.10, 0.30))
            pyautogui.press(key)
            if self.fast_mode:
                time.sleep(random.uniform(0.10, 0.25))
            else:
                time.sleep(random.uniform(0.20, 0.50))
            return True
        except Exception as e:
            print(f"Error pressing key '{key}': {e}")
            return False
    
    def check_break_time(self):
        """Check if it's time for a break"""
        current_time = time.time()
        session_time = current_time - self.session_start_time
        time_since_last_break = current_time - self.last_break_time
        
        # For non-debug, periodically print a concise status line
        if not self.debug:
            next_break_in = max(0, int(self.break_interval - time_since_last_break))
            next_break_min = next_break_in // 60
            next_break_sec = next_break_in % 60
            # Estimate alchs per hour factoring break ratio so far
            elapsed = max(1e-6, current_time - self.session_start_time)
            effective_time = max(1e-6, elapsed - self.total_break_time)
            alchs_per_hour = (self.click_count / effective_time) * 3600.0
            print(
                f"Alchs: {self.click_count} | Recoveries: {self.messed_up_count} | Next break in {next_break_min}m {next_break_sec}s (duration {self.break_duration}s) | ~{alchs_per_hour:.1f} alchs/hr"
            )

        if time_since_last_break >= self.break_interval:
            if self.debug:
                print(f"   ☕ Break time! Taking a {self.break_duration} second break...")
                print(f"   📊 Session stats: {self.click_count} clicks in {session_time/60:.1f} minutes")
            before = time.time()
            time.sleep(self.break_duration)
            self.total_break_time += time.time() - before
            self.last_break_time = current_time
            self.break_interval = random.randint(600, 1200)  # New random interval
            if self.debug:
                print("   ✅ Break finished, resuming...")
            return True
        return False
    
    def capture_screen(self):
        """Capture current screen"""
        try:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            # Update scale factors (image pixels vs OS coordinates)
            try:
                sw, sh = pyautogui.size()
                ih, iw = frame.shape[:2]
                self.scale_x = max(1e-6, iw / float(sw))
                self.scale_y = max(1e-6, ih / float(sh))
                if self.debug:
                    print(f"   🧪 Scale factors: scale_x={self.scale_x:.3f}, scale_y={self.scale_y:.3f} (img {iw}x{ih}, os {sw}x{sh})")
            except Exception:
                self.scale_x = self.scale_y = 1.0
            return frame
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def _to_screen_coords(self, pos):
        """Convert image pixel coordinates to OS screen points"""
        x, y = pos
        sx = int(round(x / max(1e-6, self.scale_x)))
        sy = int(round(y / max(1e-6, self.scale_y)))
        return (sx, sy)
    
    def on_key_press(self, key):
        """Handle key press events"""
        try:
            if key.char == 'p':
                self.is_paused = not self.is_paused
                if self.is_paused:
                    print("\n⏸️  Script PAUSED - Press 'p' again to resume...")
                else:
                    print("\n▶️  Script RESUMED...")
                time.sleep(0.3)  # Prevent multiple toggles
        except AttributeError:
            pass
    
    def start_keyboard_listener(self):
        """Start keyboard listener for pause functionality"""
        try:
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            self.keyboard_listener.start()
            print("✅ Keyboard listener started - Press 'p' to pause/resume")
        except Exception as e:
            print(f"⚠️  Could not start keyboard listener: {e}")
            print("   Pause functionality will not be available")
    
    def move_mouse_away_from_spells(self):
        """Move mouse away from spells to clear potential popups"""
        try:
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Calculate new position (move ~200 pixels left)
            new_x = current_x - random.randint(180, 220)  # Random variation for humanization
            
            # Keep mouse within screen bounds
            screen_width, screen_height = pyautogui.size()
            new_x = max(50, min(new_x, screen_width - 50))  # Keep away from edges
            
            # Human-like movement duration
            distance = abs(new_x - current_x)
            movement_duration = random.uniform(0.2, 0.4)  # Quick but natural movement
            
            # Move mouse with slight curve for natural movement
            waypoint_x = current_x + (new_x - current_x) * random.uniform(0.3, 0.7)
            waypoint_y = current_y + random.randint(-10, 10)  # Slight vertical variation
            
            # Move through waypoint to target
            pyautogui.moveTo(waypoint_x, waypoint_y, duration=movement_duration * 0.6)
            pyautogui.moveTo(new_x, current_y, duration=movement_duration * 0.4)
            
            if self.debug:
                print(f"   🖱️  Moved mouse from ({current_x}, {current_y}) to ({new_x}, {current_y}) to clear popup")
            
        except Exception as e:
            print(f"   ❌ Error moving mouse: {e}")
    
    def recover_from_inventory(self):
        """Recover from stuck state by checking inventory for darts"""
        try:
            print("   📦 Opening inventory to look for darts...")
            # First try the inventory tab (key '0')
            self.press_key(self.key_inventory, "open inventory tab")
            time.sleep(0.5)
            
            # Capture screen after opening inventory
            screen = self.capture_screen()
            if screen is None:
                print("   ❌ Could not capture screen for inventory recovery")
                return False
            
            # Look for darts in inventory (try all dart templates)
            print("   🔍 Looking for darts in inventory...")
            dart_position, dart_confidence = None, 0.0
            for tmpl, name in (self.dart_templates or []):
                pos, conf = self.find_template(screen, tmpl, threshold=0.55)
                if conf > dart_confidence and pos is not None:
                    dart_position, dart_confidence = pos, conf
                    best_name = name
            
            if dart_position and dart_confidence > 0.55:
                print(f"   🎯 Found darts in inventory using {best_name} (confidence: {dart_confidence:.2f})")
                if self.human_click(dart_position, "🎯 Clicked darts in inventory"):
                    print("   ✅ Successfully clicked darts in inventory")
                    
                    # Wait and check that darts are no longer visible on screen (faster)
                    print("   ⏳ Waiting to confirm darts are no longer visible...")
                    max_checks = 4  # Check up to 4 times (2 seconds)
                    darts_disappeared = False
                    for check in range(max_checks):
                        time.sleep(0.3)  # Faster checks
                        screen = self.capture_screen()
                        if screen is None:
                            continue
                        
                        # Check if darts are still visible
                        check_pos, check_conf = None, 0.0
                        for tmpl, _nm in (self.dart_templates or []):
                            pos, conf = self.find_template(screen, tmpl, threshold=0.55)
                            if conf > check_conf and pos is not None:
                                check_pos, check_conf = pos, conf
                        dart_position, dart_confidence = check_pos, check_conf
                        if dart_position is None or dart_confidence < 0.55:
                            print(f"   ✅ Darts no longer visible on screen (check {check + 1}/{max_checks})")
                            darts_disappeared = True
                            break
                        else:
                            print(f"   🔍 Darts still visible (confidence: {dart_confidence:.2f}), waiting...")
                    
                    # If darts didn't disappear, try clicking again (faster)
                    if not darts_disappeared:
                        print("   ⚠️  Darts still visible after clicking, trying one more time...")
                        screen = self.capture_screen()
                        if screen is not None:
                            retry_pos, retry_conf = None, 0.0
                            for tmpl, _nm in (self.dart_templates or []):
                                pos, conf = self.find_template(screen, tmpl, threshold=0.55)
                                if conf > retry_conf and pos is not None:
                                    retry_pos, retry_conf = pos, conf
                            dart_position, dart_confidence = retry_pos, retry_conf
                            if dart_position and dart_confidence > 0.55:
                                print(f"   🎯 Clicking darts again (confidence: {dart_confidence:.2f})")
                                self.human_click(dart_position, "🎯 Clicked darts in inventory (retry)")
                                time.sleep(0.5)  # Shorter wait after second click
                    
                    # Now go back to spellbook
                    print("   📚 Returning to spellbook...")
                    self.press_key(self.key_spellbook, "open spellbook")
                    time.sleep(0.3)  # Faster return to spellbook
                    return True
            else:
                print(f"   ❌ No darts found in inventory (best match: {dart_confidence:.2f})")
                # Try worn equipment tab as a secondary check
                print("   🧰 Opening worn equipment tab to double-check...")
                self.press_key(self.key_equipment, "open worn equipment tab")
                time.sleep(0.5)
                screen = self.capture_screen()
                if screen is not None:
                    print("   🔍 Looking for dart icon on equipment tab...")
                    eq_pos, eq_conf = None, 0.0
                    for tmpl, _nm in (self.dart_templates or []):
                        pos, conf = self.find_template(screen, tmpl, threshold=0.55)
                        if conf > eq_conf and pos is not None:
                            eq_pos, eq_conf = pos, conf
                    if eq_pos and eq_conf > 0.55:
                        print(f"   🎯 Found dart-like icon on equipment tab (confidence: {eq_conf:.2f})")
                        # Click to unequip to inventory, confirm disappearance
                        if self.human_click(eq_pos, "🎯 Clicked darts on worn equipment"):
                            print("   ⏳ Waiting for darts to leave worn equipment...")
                            max_checks = 4
                            for check in range(max_checks):
                                time.sleep(0.3)
                                screen = self.capture_screen()
                                if screen is None:
                                    continue
                                eq_check_pos, eq_check_conf = None, 0.0
                                for tmpl, _nm in (self.dart_templates or []):
                                    pos, conf = self.find_template(screen, tmpl, threshold=0.55)
                                    if conf > eq_check_conf and pos is not None:
                                        eq_check_pos, eq_check_conf = pos, conf
                                if not eq_check_pos or eq_check_conf < 0.55:
                                    print(f"   ✅ Darts no longer in worn equipment (check {check+1}/{max_checks})")
                                    break
                                else:
                                    print(f"   🔍 Darts still in worn equipment (confidence: {eq_check_conf:.2f}), retrying click...")
                                    self.human_click(eq_check_pos, "🎯 Clicked darts on worn equipment (retry)")
                        # After unequip attempts, switch to inventory and verify presence
                        print("   📦 Switching to inventory to verify darts are present...")
                        self.press_key(self.key_inventory, "open inventory tab")
                        time.sleep(0.3)
                        inv_screen = self.capture_screen()
                        inventory_has_darts = False
                        if inv_screen is not None:
                            inv_pos, inv_conf = None, 0.0
                            for tmpl, _nm in (self.dart_templates or []):
                                pos, conf = self.find_template(inv_screen, tmpl, threshold=0.55)
                                if conf > inv_conf and pos is not None:
                                    inv_pos, inv_conf = pos, conf
                            if inv_pos and inv_conf > 0.55:
                                print(f"   ✅ Darts detected in inventory (confidence: {inv_conf:.2f})")
                                inventory_has_darts = True
                            else:
                                print(f"   ⚠️  Darts not detected in inventory (best match: {inv_conf if 'inv_conf' in locals() else 0.0:.2f})")
                    else:
                        print(f"   ❌ No dart-like icon on equipment tab (best match: {eq_conf if 'eq_conf' in locals() else 0.0:.2f})")
                # Return to spellbook
                print("   📚 Returning to spellbook...")
                self.press_key(self.key_spellbook, "open spellbook")
                time.sleep(0.5)
                # If we successfully moved darts to inventory, signal recovery success and count as messed up
                success = True if 'inventory_has_darts' in locals() and inventory_has_darts else False
                if success:
                    self.messed_up_count += 1
                return success
                
        except Exception as e:
            print(f"   ❌ Error during inventory recovery: {e}")
            return False
    
    def start(self):
        """Start the auto alch process"""
        print("🤖 Simple Auto Alch - Alch Spell + Darts")
        print("=" * 50)
        print("Steps:")
        print("1. Find and click alch spell")
        print("2. Find and click darts")
        print("3. Repeat")
        print()
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner for emergency stop.")
        print("Press 'p' to pause/resume the script.")
        print(f"⏰ Break every {self.break_interval/60:.1f} minutes")
        print()
        
        # Load templates
        if not self.load_templates():
            return
        
        # Start keyboard listener for pause functionality
        self.start_keyboard_listener()
        if self.is_paused:
            print("⏸️  Script PAUSED - Click game and press 'p' to start...")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Check if script is paused
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                
                # Check for break time
                self.check_break_time()
                
                # Capture screen
                screen = self.capture_screen()
                if screen is None:
                    continue
                
                if self.waiting_for_alch_spell:
                    if self.debug:
                        print("   🔍 Looking for alch spell...")
                    
                    # First: try to detect without pressing the spellbook key
                    alch_position, alch_confidence = self.find_alch_spell(screen)
                    if alch_position and (alch_confidence >= 0.68):
                        if self.debug:
                            print(f"   🔮 Found alch spell (confidence: {alch_confidence:.2f})")
                        if self.human_click(alch_position, "🔮 Clicked alch spell"):
                            self.waiting_for_alch_spell = False
                            self.waiting_for_darts = True
                            self.alch_armed = True
                            if self.debug:
                                print("   🔄 Now looking for darts...")
                    else:
                        if self.debug:
                            print(f"   ℹ️  No alch found yet (best {alch_confidence if 'alch_confidence' in locals() else 0.0:.2f} < 0.68). Pressing '{self.key_spellbook}' to open spellbook and retry...")
                        # Press spellbook key and retry once
                        self.press_key(self.key_spellbook, "open spellbook")
                        time.sleep(0.3)
                        screen = self.capture_screen()
                        if screen is not None:
                            alch_position, alch_confidence = self.find_alch_spell(screen)
                            if alch_position and (alch_confidence >= 0.68):
                                if self.debug:
                                    print(f"   🔮 Found alch spell (confidence: {alch_confidence:.2f})")
                                if self.human_click(alch_position, "🔮 Clicked alch spell"):
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_darts = True
                                    self.alch_armed = True
                                    if self.debug:
                                        print("   🔄 Now looking for darts...")
                            else:
                                if self.debug:
                                    print(f"   ℹ️  Still no alch (best {alch_confidence if 'alch_confidence' in locals() else 0.0:.2f}). Will clear hover and try next loop...")
                                self.move_mouse_away_from_spells()
                                time.sleep(0.2)
                
                elif self.waiting_for_darts:
                    if self.debug:
                        print("   🔍 Looking for darts...")
                    dart_position, dart_confidence = self.find_darts(screen)
                    
                    if dart_position and dart_confidence > 0.55:
                        if self.debug:
                            print(f"   🎯 Found darts (confidence: {dart_confidence:.2f})")
                        # Only click darts if alch was just clicked (armed)
                        if not self.alch_armed:
                            if self.debug:
                                print("   ⚠️  Skipping darts click because alch is not armed.")
                            time.sleep(0.2)
                            continue
                        # Optional tiny hover in fast mode
                        try:
                            hover_duration = random.uniform(self.darts_hover_min, self.darts_hover_max)
                            if hover_duration > 0:
                                sx, sy = self._to_screen_coords(dart_position)
                                pyautogui.moveTo(sx, sy, duration=hover_duration)
                                time.sleep(random.uniform(self.click_pause_min, self.click_pause_max))
                        except Exception:
                            pass
                        if self.human_click(dart_position, "🎯 Clicked darts"):
                            # Immediately try to re-arm by finding the alch spell again
                            if self.debug:
                                print("   🔁 Re-arming: scanning for alch spell immediately...")
                            start_time = time.time()
                            rearmed = False
                            prev_pos = None
                            while time.time() - start_time < self.rearm_timeout_sec:
                                frame2 = self.capture_screen()
                                if frame2 is None:
                                    time.sleep(0.05)
                                    continue
                                # Re-arm: Prefer the strongest template 'alc-spell4.png' only
                                pos2, conf2 = None, 0.0
                                for tmpl, label in (self.alch_templates or []):
                                    if label.lower() != "alc-spell4.png":
                                        continue
                                    p4, c4 = self.find_template_multiscale(frame2, tmpl)
                                    if c4 > conf2 and p4 is not None:
                                        pos2, conf2 = p4, c4
                                if pos2 and conf2 >= self.rearm_spell4_threshold:
                                    if self.debug:
                                        print(f"   ⚡ Re-armed: found alc-spell4 (conf {conf2:.2f}) — clicking immediately")
                                    self.human_click(pos2, "🔮 Clicked alch spell (chain) — spell4")
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_darts = True
                                    self.alch_armed = True
                                    rearmed = True
                                    break
                                # If moderately confident on spell4 and stable across consecutive frames, accept
                                if pos2 and conf2 >= (self.rearm_spell4_threshold - 0.10) and prev_pos is not None:
                                    if abs(pos2[0] - prev_pos[0]) <= 16 and abs(pos2[1] - prev_pos[1]) <= 16:
                                        if self.debug:
                                            print(f"   ⚡ Re-armed (stable spell4): conf {conf2:.2f} — clicking")
                                        self.human_click(pos2, "🔮 Clicked alch spell (chain-stable) — spell4")
                                        self.waiting_for_alch_spell = False
                                        self.waiting_for_darts = True
                                        self.alch_armed = True
                                        rearmed = True
                                        break
                                prev_pos = pos2 if pos2 else prev_pos
                                time.sleep(random.uniform(self.rearm_poll_min, self.rearm_poll_max))

                            # If not re-armed quickly, fallback to a short wait and resume normal loop
                            if not rearmed:
                                if self.debug:
                                    print("   ⏳ Fallback wait before next cycle...")
                                time.sleep(random.uniform(self.post_dart_wait_min, self.post_dart_wait_max))
                                self.waiting_for_alch_spell = True
                                self.waiting_for_darts = False
                                self.alch_armed = False

                            self.click_count += 1
                            if self.debug:
                                print(f"   📊 Total clicks: {self.click_count}")
                            self.dart_fail_count = 0  # Reset fail count on success
                            if self.debug:
                                print("   🔄 Now looking for alch spell...")
                    else:
                        self.dart_fail_count += 1
                        if self.debug:
                            print(f"   🔍 Darts not found (best match: {dart_confidence:.2f}), attempt {self.dart_fail_count}/{self.max_dart_fails}")
                        
                        # If we've failed too many times, try inventory recovery
                        if self.dart_fail_count >= self.max_dart_fails:
                            if self.debug:
                                print("   🚨 Too many dart failures - attempting inventory recovery...")
                            if self.recover_from_inventory():
                                self.dart_fail_count = 0  # Reset counter
                                self.waiting_for_alch_spell = True
                                self.waiting_for_darts = False
                                self.alch_armed = False
                                if self.debug:
                                    print("   ✅ Recovery successful - returning to alch spell...")
                            else:
                                if self.debug:
                                    print("   ❌ Recovery failed - continuing to retry...")
                                self.dart_fail_count = 0  # Reset counter to try again
                        else:
                            time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping Auto Alch...")
                session_time = time.time() - self.session_start_time
                print(f"📊 Session stats:")
                print(f"   - Total clicks: {self.click_count}")
                print(f"   - Session time: {session_time/60:.1f} minutes")
                print(f"   - Clicks per minute: {self.click_count/(session_time/60):.1f}")
                self.is_running = False
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
        
        # Stop keyboard listener
        if self.keyboard_listener:
            self.keyboard_listener.stop()

def main():
    """Main function"""
    print("Starting Simple Auto Alch...")
    
    # Check imports
    try:
        import cv2
        import pyautogui
        import numpy as np
        from pynput import keyboard
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Install with: pip install opencv-python pyautogui numpy pynput")
        return
    
    # Create and start
    alch = SimpleAutoAlch()
    alch.start()

if __name__ == "__main__":
    main()
