# Config-Specific Template Organization

## Overview

The bot now organizes templates into config-specific folders to prevent naming conflicts when using multiple configurations. Each config file now has its own dedicated template directory.

## New Directory Structure

```
templates/
├── default/                 # Templates for default_config.json
│   ├── template1.png
│   └── template2.png
├── my_config/              # Templates for my_config.json
│   ├── template1.png       # Can have same name as default/template1.png
│   └── template3.png
├── ssloj/                  # Templates for ssloj.json
│   ├── seed_complete.png
│   └── seed_xp.png
└── pumpkin_panic/          # Templates for pumpkin_panic.json
    ├── ready.png
    └── game_running.png
```

## Key Changes Made

### 1. Config Manager (`modules/config_manager.py`)

- ✅ Added `get_templates_dir()` method to return config-specific template directory
- ✅ Added `migrate_templates_to_config()` method to auto-migrate templates
- ✅ Added `current_config_filename` tracking
- ✅ Updated all template path references to use config-specific directories
- ✅ Modified `load_config()` to automatically migrate templates when loading
- ✅ Modified `save_config()` to track current config filename

### 2. Image Detector (`modules/image_detector.py`)

- ✅ Added `update_templates_dir()` method to switch template directories
- ✅ Template cache automatically clears when directory changes

### 3. Main Application (`app.py`)

- ✅ Added `_update_templates_directory()` method
- ✅ Updated config loading to refresh template directories
- ✅ Updated config saving to refresh template directories
- ✅ Updated template browsing to use config-specific directories
- ✅ Updated template importing to use config-specific directories
- ✅ Updated debug information to show correct template paths
- ✅ Updated rules list to check templates in correct directories
- ✅ **Added "New Game" button for easy new configuration creation**

### 4. Migration Tool (`migrate_templates.py`)

- ✅ Created migration script to help transition existing setups
- ✅ Supports preview mode to see what would be migrated
- ✅ Preserves original templates in base directory

## How It Works

1. **Automatic Migration**: When you load a config, the system automatically:

   - Creates a config-specific template folder (`templates/config_name/`)
   - Copies relevant templates from the base `templates/` directory
   - Updates the image detector to use the new directory

2. **Config-Specific Isolation**: Each config file gets its own template folder:

   - `default_config.json` → `templates/default/`
   - `my_config.json` → `templates/my_config/`
   - `ssloj.json` → `templates/ssloj/`

3. **Template Deduplication**: Templates are only copied if they're referenced in the config's detection rules.

## Benefits

### ✅ **Naming Conflict Resolution**

- Multiple configs can have templates with the same filename
- No more "template1.png" vs "template1_config2.png" naming

### ✅ **Better Organization**

- Templates are grouped by their intended use case
- Easier to manage templates for different games/applications

### ✅ **Automatic Migration**

- Existing setups are automatically migrated
- No manual work required

### ✅ **Backward Compatibility**

- Original templates remain in base directory
- Migration is non-destructive

## Usage Instructions

### For Existing Users

1. **Automatic Migration** (Recommended):

   - Simply load a config file in the application
   - Templates will be automatically migrated to config-specific folders

2. **Manual Migration** (Optional):

   ```bash
   # Preview what would be migrated
   python migrate_templates.py --preview

   # Run the migration
   python migrate_templates.py
   ```

### For New Users

1. **Create New Game Configuration**:

   - Click the **"New Game"** button in the Configuration tab
   - Enter game name, window title, and target resolution
   - System automatically creates config file and template directory
   - Ready to start adding templates and rules!

2. **Alternative Method**:
   - Create a new config file manually
   - Import templates using the "Import Templates" button
   - Templates will automatically go to the correct config-specific folder

### Managing Templates

- **Browse Templates**: Shows templates for the currently loaded config
- **Import Templates**: Adds templates to the current config's directory
- **Template Statistics**: Reports on templates in the current config's directory

## Migration Process

The migration happens in these steps:

1. **Config Loading**: When you load a config file
2. **Directory Creation**: Creates `templates/config_name/` if needed
3. **Template Analysis**: Scans detection rules for required templates
4. **Template Copying**: Copies matching templates from base directory
5. **Detector Update**: Updates image detector to use new directory

## Example Workflow

```bash
# Before: All templates in one folder
templates/
├── ready.png
├── game_running.png
├── seed_complete.png
└── claim.png

# After loading different configs:
templates/
├── ready.png                    # Original preserved
├── game_running.png             # Original preserved
├── seed_complete.png            # Original preserved
├── claim.png                    # Original preserved
├── default/                     # For default_config.json
│   ├── ready.png               # Copy for default config
│   └── game_running.png        # Copy for default config
└── ssloj/                      # For ssloj.json
    ├── seed_complete.png       # Copy for ssloj config
    └── claim.png               # Copy for ssloj config
```

## 🎮 New Game Setup Workflow

The **"New Game"** button provides a streamlined way to set up configurations for new games:

### Step-by-Step Process

1. **Click "New Game"** in the Configuration tab
2. **Enter Game Details**:

   - **Game Name**: Display name for your configuration
   - **Window Title**: Partial match for the game window (e.g., "Stumble", "Xbox")
   - **Target Resolution**: Game window size (common presets available)

3. **Automatic Setup**:

   - Creates `game_name.json` config file
   - Creates `templates/game_name/` directory
   - Resets all settings to defaults
   - Sets window and resolution configuration
   - Selects new config as active

4. **Ready to Configure**:
   - Import templates specific to this game
   - Create detection rules for game events
   - Configure bot actions and sequences

### Example: Setting Up "Pumpkin Panic"

```
1. Click "New Game"
2. Enter:
   - Game Name: "Pumpkin Panic"
   - Window Title: "Pumpkin"
   - Resolution: 1280x720
3. Results in:
   - File: configs/pumpkin_panic.json
   - Directory: templates/pumpkin_panic/
   - Clean slate ready for templates and rules
```

## Troubleshooting

### Templates Not Found

- Ensure you've loaded the correct config file
- Check that templates exist in the config-specific directory
- Use the migration tool if templates are still in the base directory

### Wrong Templates Directory

- The system automatically updates when you load/save configs
- Restart the application if templates seem to be from wrong config

### Migration Issues

- Use `python migrate_templates.py --preview` to diagnose
- Original templates are never deleted, only copied
- You can always manually copy templates between config directories

## Technical Details

### Template Path Resolution

```python
# Old way (single directory)
template_path = os.path.join("templates", template_name)

# New way (config-specific)
templates_dir = config_manager.get_templates_dir()
template_path = os.path.join(templates_dir, template_name)
```

### Directory Naming Convention

- Config filename: `my_awesome_bot.json`
- Template directory: `templates/my_awesome_bot/`
- Extension (.json) is automatically removed

### Cache Management

- Template cache is cleared when switching configs
- Ensures templates are loaded from correct directory
- No stale template data between config switches
