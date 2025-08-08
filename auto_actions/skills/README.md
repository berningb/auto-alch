# Template Images Guide

This directory contains template images used for skill detection in the auto functions.

## Current Templates

- `stats.png` - Full stats page template for detection
- `skills/` - Individual skill icon templates (create these)

## Creating Skill Templates

To use the `checkstats` function, you need individual skill templates. Here's how to create them:

### Method 1: Manual Creation
1. Open RuneScape and go to the stats page (press '4')
2. Take screenshots of individual skill icons
3. Save them as `.png` files in the `skills/` directory
4. Name them exactly as the skill name (lowercase):
   - `attack.png`
   - `strength.png` 
   - `defence.png`
   - `ranged.png`
   - `prayer.png`
   - `magic.png`
   - etc.

### Method 2: Using the Template Creator Tool
1. Take a screenshot of your full stats page
2. Save it as `stats_full.png` in this images directory
3. Run the template creator: `python create_skill_templates.py`
4. Follow the interactive prompts to select each skill

## All 23 Skills Needed

You'll need templates for all these skills:

**Combat Skills:**
- attack.png
- strength.png  
- defence.png
- ranged.png
- prayer.png
- magic.png
- hitpoints.png

**Gathering Skills:**
- mining.png
- fishing.png
- woodcutting.png
- farming.png
- hunter.png

**Artisan Skills:**
- crafting.png
- fletching.png
- smithing.png
- cooking.png
- firemaking.png
- runecrafting.png
- construction.png

**Support Skills:**
- agility.png
- herblore.png
- thieving.png
- slayer.png

## Template Tips

- **Size**: Keep skill icons small (around 20-40 pixels)
- **Quality**: Use clear, high-contrast images
- **Background**: Try to exclude background elements
- **Consistency**: Use the same zoom level for all templates

## Testing Templates

After creating templates, test them with:
```bash
python quick_test.py
```

The test will show which skills are detected and their confidence levels.
