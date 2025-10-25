#!/usr/bin/env python3
"""
Template Migration Script

This script helps migrate existing templates from the old single templates/ 
directory to the new config-specific template structure.
"""

import os
import shutil
import json
from pathlib import Path

def migrate_templates_for_all_configs():
    """Migrate templates for all existing config files."""
    
    print("🔄 Starting template migration...")
    
    # Directories
    configs_dir = "configs"
    base_templates_dir = "templates"
    
    if not os.path.exists(configs_dir):
        print("❌ No configs directory found!")
        return
    
    if not os.path.exists(base_templates_dir):
        print("❌ No templates directory found!")
        return
    
    # Get all config files
    config_files = [f for f in os.listdir(configs_dir) if f.endswith('.json')]
    
    if not config_files:
        print("❌ No config files found!")
        return
    
    print(f"📁 Found {len(config_files)} config files:")
    for config_file in config_files:
        print(f"   - {config_file}")
    
    total_migrated = 0
    
    for config_file in config_files:
        print(f"\n🔧 Processing {config_file}...")
        migrated_count = migrate_templates_for_config(config_file)
        total_migrated += migrated_count
        print(f"   ✅ Migrated {migrated_count} templates")
    
    print(f"\n🎉 Migration complete! Total templates migrated: {total_migrated}")
    print("\n📝 Next steps:")
    print("   1. Start the application")
    print("   2. Load a config - templates will be automatically organized")
    print("   3. Old templates in base templates/ directory are preserved")

def migrate_templates_for_config(config_filename):
    """Migrate templates for a specific config file."""
    
    try:
        # Load config to get template names
        config_path = os.path.join("configs", config_filename)
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        detection_rules = config_data.get('detection_rules', [])
        templates_to_migrate = set()
        
        # Collect template names from rules
        for rule in detection_rules:
            template_name = rule.get('template', '')
            if template_name:
                # Ensure .png extension
                if not template_name.endswith('.png'):
                    template_name += '.png'
                templates_to_migrate.add(template_name)
        
        if not templates_to_migrate:
            return 0
        
        # Create config-specific templates directory
        config_name = os.path.splitext(config_filename)[0]
        config_templates_dir = os.path.join("templates", config_name)
        os.makedirs(config_templates_dir, exist_ok=True)
        
        # Copy templates
        migrated_count = 0
        for template_name in templates_to_migrate:
            source_path = os.path.join("templates", template_name)
            dest_path = os.path.join(config_templates_dir, template_name)
            
            if os.path.exists(source_path) and not os.path.exists(dest_path):
                shutil.copy2(source_path, dest_path)
                migrated_count += 1
                print(f"      📄 {template_name}")
        
        return migrated_count
        
    except Exception as e:
        print(f"      ❌ Error processing {config_filename}: {e}")
        return 0

def preview_migration():
    """Preview what templates would be migrated without actually doing it."""
    
    print("🔍 Migration Preview:")
    print("=" * 50)
    
    configs_dir = "configs"
    base_templates_dir = "templates"
    
    if not os.path.exists(configs_dir) or not os.path.exists(base_templates_dir):
        print("❌ Required directories not found!")
        return
    
    config_files = [f for f in os.listdir(configs_dir) if f.endswith('.json')]
    
    for config_file in config_files:
        print(f"\n📋 Config: {config_file}")
        
        try:
            config_path = os.path.join(configs_dir, config_file)
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            detection_rules = config_data.get('detection_rules', [])
            templates_needed = set()
            
            for rule in detection_rules:
                template_name = rule.get('template', '')
                if template_name:
                    if not template_name.endswith('.png'):
                        template_name += '.png'
                    templates_needed.add(template_name)
            
            if templates_needed:
                config_name = os.path.splitext(config_file)[0]
                target_dir = os.path.join("templates", config_name)
                print(f"   → Target directory: {target_dir}")
                
                existing_count = 0
                missing_count = 0
                
                for template_name in sorted(templates_needed):
                    source_path = os.path.join("templates", template_name)
                    if os.path.exists(source_path):
                        print(f"   ✅ {template_name}")
                        existing_count += 1
                    else:
                        print(f"   ❌ {template_name} (missing)")
                        missing_count += 1
                
                print(f"   📊 Summary: {existing_count} available, {missing_count} missing")
            else:
                print("   📭 No templates needed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_migration()
    else:
        print("Template Migration Tool")
        print("=" * 30)
        print()
        print("This tool will:")
        print("1. Analyze your config files")
        print("2. Create config-specific template directories")
        print("3. Copy relevant templates to each config directory")
        print()
        
        choice = input("Continue with migration? (y/N): ").strip().lower()
        if choice in ['y', 'yes']:
            migrate_templates_for_all_configs()
        else:
            print("Migration cancelled.")
            print()
            print("To preview what would be migrated, run:")
            print("python migrate_templates.py --preview")