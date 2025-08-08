#!/usr/bin/env python3
"""
Skill Template Creator
Help create individual skill templates from a stats page screenshot
"""

import cv2
import numpy as np
import os
from pathlib import Path

def create_skill_templates():
    """
    Interactive tool to help create skill templates
    """
    print("🎯 Skill Template Creator")
    print("=" * 50)
    print("This tool will help you create individual skill templates.")
    print()
    print("📋 Steps:")
    print("1. Take a screenshot of your stats page")
    print("2. Save it as 'stats_full.png' in the images/ directory")
    print("3. Run this tool to extract individual skills")
    print()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(current_dir, "images")
    skills_dir = os.path.join(images_dir, "skills")
    
    # Check if stats screenshot exists
    stats_full_path = os.path.join(images_dir, "stats_full.png")
    
    if not os.path.exists(stats_full_path):
        print(f"❌ Screenshot not found at: {stats_full_path}")
        print("📝 Please:")
        print("   1. Open RuneScape and go to stats page")
        print("   2. Take a screenshot and save as 'stats_full.png' in images/ directory")
        print("   3. Run this script again")
        return
    
    # Load the screenshot
    stats_image = cv2.imread(stats_full_path)
    if stats_image is None:
        print(f"❌ Could not load image: {stats_full_path}")
        return
    
    print(f"✅ Loaded stats screenshot: {stats_image.shape}")
    
    # Ensure skills directory exists
    Path(skills_dir).mkdir(exist_ok=True)
    
    # List of all RuneScape skills
    skills = [
        'attack', 'strength', 'defence', 'ranged', 'prayer', 'magic',
        'runecrafting', 'construction', 'hitpoints', 'agility', 'herblore', 'thieving',
        'crafting', 'fletching', 'slayer', 'hunter', 'mining', 'smithing',
        'fishing', 'cooking', 'firemaking', 'woodcutting', 'farming'
    ]
    
    print(f"\n📋 Need to extract {len(skills)} skills:")
    for i, skill in enumerate(skills, 1):
        print(f"   {i:2d}. {skill.title()}")
    
    print(f"\n🖼️ The screenshot will be displayed with click interface.")
    print("📝 Instructions:")
    print("   - Click and drag to select each skill icon")
    print("   - Press 's' to save the selection")
    print("   - Press 'n' to skip to next skill")
    print("   - Press 'q' to quit")
    
    # Interactive extraction
    extract_skills_interactive(stats_image, skills, skills_dir)

def extract_skills_interactive(image, skills, output_dir):
    """
    Interactive skill extraction with mouse selection
    """
    current_skill_idx = 0
    
    # Variables for mouse selection
    selecting = False
    start_point = None
    end_point = None
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal selecting, start_point, end_point, display_image
        
        if event == cv2.EVENT_LBUTTONDOWN:
            selecting = True
            start_point = (x, y)
            end_point = (x, y)
        
        elif event == cv2.EVENT_MOUSEMOVE and selecting:
            end_point = (x, y)
            
        elif event == cv2.EVENT_LBUTTONUP:
            selecting = False
            end_point = (x, y)
    
    cv2.namedWindow('Stats Screenshot - Select Skills', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('Stats Screenshot - Select Skills', mouse_callback)
    
    while current_skill_idx < len(skills):
        skill_name = skills[current_skill_idx]
        
        # Create display image
        display_image = image.copy()
        
        # Draw selection rectangle if selecting
        if start_point and end_point:
            cv2.rectangle(display_image, start_point, end_point, (0, 255, 0), 2)
        
        # Add text overlay
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"Select {skill_name.title()} ({current_skill_idx + 1}/{len(skills)})"
        cv2.putText(display_image, text, (10, 30), font, 0.8, (255, 255, 255), 2)
        cv2.putText(display_image, "Press 's' to save, 'n' to skip, 'q' to quit", (10, 60), font, 0.6, (255, 255, 255), 2)
        
        cv2.imshow('Stats Screenshot - Select Skills', display_image)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s') and start_point and end_point:
            # Save the selected area
            x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
            x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])
            
            if x2 > x1 and y2 > y1:  # Valid selection
                skill_crop = image[y1:y2, x1:x2]
                skill_path = os.path.join(output_dir, f"{skill_name}.png")
                cv2.imwrite(skill_path, skill_crop)
                print(f"✅ Saved {skill_name}.png ({skill_crop.shape})")
                
                current_skill_idx += 1
                start_point = None
                end_point = None
            else:
                print(f"❌ Invalid selection for {skill_name}")
        
        elif key == ord('n'):
            # Skip this skill
            print(f"⏭️ Skipped {skill_name}")
            current_skill_idx += 1
            start_point = None
            end_point = None
        
        elif key == ord('q'):
            print("👋 Quitting extraction")
            break
    
    cv2.destroyAllWindows()
    print(f"\n🎉 Extraction complete! Created {current_skill_idx} skill templates.")

def list_existing_templates():
    """List existing skill templates"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(current_dir, "images", "skills")
    
    if not os.path.exists(skills_dir):
        print("❌ Skills directory doesn't exist")
        return []
    
    templates = [f.replace('.png', '') for f in os.listdir(skills_dir) if f.endswith('.png')]
    
    if templates:
        print(f"📁 Existing templates ({len(templates)}):")
        for template in sorted(templates):
            print(f"   ✅ {template}")
    else:
        print("📁 No existing templates found")
    
    return templates

def main():
    """Main function"""
    print("🛠️ Skill Template Management")
    print("=" * 40)
    
    choice = input("\nChoose an option:\n1. List existing templates\n2. Create new templates\n3. Exit\n\nChoice (1-3): ").strip()
    
    if choice == '1':
        list_existing_templates()
    elif choice == '2':
        create_skill_templates()
    elif choice == '3':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
