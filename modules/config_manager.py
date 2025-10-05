"""
Configuration Manager Module

Handles saving and loading of bot configuration including rules,
window settings, and other application preferences.
Provides validation, import/export, and template management functionality.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import shutil


@dataclass
class DetectionRule:
    """Data class for detection rules."""
    name: str
    template: str
    confidence: float
    action: str
    input_mode: str = "controller"  # "controller", "keyboard", or "mouse"
    enabled: bool = True
    # Cycle tracking fields
    is_cycle_marker: bool = False  # Mark this template as a cycle start/end marker
    cycle_type: str = "none"  # "start", "end", "checkpoint", "none"
    cycle_name: str = ""  # Name of the mission/cycle (e.g., "MainMission", "DailyQuest")
    expected_cycle_time: float = 0.0  # Expected time in seconds for this cycle
    cycle_tolerance: float = 0.3  # Tolerance for cycle detection (30% by default)


@dataclass
class WindowConfig:
    """Data class for window configuration."""
    window_title: str = "Xbox"
    target_width: int = 1280
    target_height: int = 720


@dataclass
class BotConfig:
    """Data class for bot timing configuration."""
    loop_delay: float = 0.1
    action_cooldown: float = 1.0
    capture_area_width: int = 30
    capture_area_height: int = 30


@dataclass
class JoystickConfig:
    """Data class for joystick configuration."""
    action_delay: float = 1.0
    auto_focus: bool = True


@dataclass
class CycleTrackingData:
    """Data class for cycle tracking information."""
    cycle_name: str
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    checkpoints: List[Dict[str, float]] = None  # List of {"name": str, "time": float}
    is_complete: bool = False
    cycle_count: int = 1
    
    def __post_init__(self):
        if self.checkpoints is None:
            self.checkpoints = []


@dataclass
class AppConfig:
    """Main application configuration."""
    version: str = "1.0.0"
    window_config: WindowConfig = None
    bot_config: BotConfig = None
    joystick_config: JoystickConfig = None
    detection_rules: List[DetectionRule] = None
    last_saved: str = ""
    # Cycle tracking
    active_cycles: List[CycleTrackingData] = None
    completed_cycles: List[CycleTrackingData] = None
    cycle_statistics: Dict[str, Dict] = None  # Stats per cycle type
    
    def __post_init__(self):
        if self.window_config is None:
            self.window_config = WindowConfig()
        if self.bot_config is None:
            self.bot_config = BotConfig()
        if self.joystick_config is None:
            self.joystick_config = JoystickConfig()
        if self.detection_rules is None:
            self.detection_rules = []
        if self.active_cycles is None:
            self.active_cycles = []
        if self.completed_cycles is None:
            self.completed_cycles = []
        if self.cycle_statistics is None:
            self.cycle_statistics = {}


class ConfigManager:
    """Manages application configuration persistence."""
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = config_dir
        self.default_config_file = "default_config.json"
        self.current_config_filename = None  # Track current config filename
        
        # Create config directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        self.current_config = AppConfig()
        
        # Create base templates directory
        self.base_templates_dir = "templates"
        if not os.path.exists(self.base_templates_dir):
            os.makedirs(self.base_templates_dir)
    
    def save_config(self, filename: Optional[str] = None) -> bool:
        """
        Save current configuration to file.
        
        Args:
            filename: Config filename. If None, uses default.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if filename is None:
                filename = self.default_config_file
            
            config_path = os.path.join(self.config_dir, filename)
            
            # Update last saved timestamp
            self.current_config.last_saved = datetime.now().isoformat()
            
            # Track current config filename
            self.current_config_filename = filename
            
            # Convert to dictionary
            config_dict = self._config_to_dict(self.current_config)
            
            # Save to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"Configuration saved to: {config_path}")
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_config(self, filename: Optional[str] = None) -> bool:
        """
        Load configuration from file.
        
        Args:
            filename: Config filename. If None, uses default.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if filename is None:
                filename = self.default_config_file
            
            config_path = os.path.join(self.config_dir, filename)
            
            if not os.path.exists(config_path):
                print(f"Config file not found: {config_path}")
                return False
            
            # Load from file
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # Convert to config object
            self.current_config = self._dict_to_config(config_dict)
            self.current_config_filename = filename  # Track current config
            
            # Migrate templates to config-specific directory if needed
            self.migrate_templates_to_config(filename)
            
            print(f"Configuration loaded from: {config_path}")
            return True
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def get_templates_dir(self, config_filename: Optional[str] = None) -> str:
        """
        Get the templates directory for a specific config.
        
        Args:
            config_filename: Config filename (without path). If None, uses current config.
            
        Returns:
            Path to the config-specific templates directory
        """
        if config_filename is None:
            config_filename = self.current_config_filename or self.default_config_file
        
        # Remove .json extension and path to get config name
        config_name = os.path.splitext(os.path.basename(config_filename))[0]
        
        # Create config-specific templates directory
        templates_dir = os.path.join(self.base_templates_dir, config_name)
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        
        return templates_dir
    
    def migrate_templates_to_config(self, config_filename: str) -> bool:
        """
        Migrate templates from the base templates directory to config-specific directory.
        
        Args:
            config_filename: Config filename to migrate templates for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_templates_dir = self.get_templates_dir(config_filename)
            
            # Get templates used by this config
            config_path = os.path.join(self.config_dir, config_filename)
            if not os.path.exists(config_path):
                return False
            
            # Load config to get template names
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            detection_rules = config_data.get('detection_rules', [])
            templates_to_migrate = set()
            
            for rule in detection_rules:
                template_name = rule.get('template', '')
                if template_name:
                    templates_to_migrate.add(template_name)
            
            # Copy templates from base directory to config directory
            imported_count = 0
            for template_name in templates_to_migrate:
                # Ensure .png extension
                if not template_name.endswith('.png'):
                    template_name += '.png'
                
                source_path = os.path.join(self.base_templates_dir, template_name)
                dest_path = os.path.join(config_templates_dir, template_name)
                
                if os.path.exists(source_path) and not os.path.exists(dest_path):
                    import shutil
                    shutil.copy2(source_path, dest_path)
                    imported_count += 1
            
            if imported_count > 0:
                print(f"Migrated {imported_count} templates for config '{config_filename}'")
            return True
            
        except Exception as e:
            print(f"Error migrating templates for config '{config_filename}': {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.current_config = AppConfig()
        print("Configuration reset to defaults")
    
    def get_config_files(self) -> List[str]:
        """
        Get list of available configuration files.
        
        Returns:
            List of config filenames
        """
        try:
            files = []
            for filename in os.listdir(self.config_dir):
                if filename.endswith('.json'):
                    files.append(filename)
            return sorted(files)
        except Exception as e:
            print(f"Error listing config files: {e}")
            return []
    
    def delete_config(self, filename: str) -> bool:
        """
        Delete a configuration file.
        
        Args:
            filename: Config filename to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_path = os.path.join(self.config_dir, filename)
            
            if os.path.exists(config_path):
                os.remove(config_path)
                print(f"Configuration deleted: {filename}")
                return True
            else:
                print(f"Config file not found: {filename}")
                return False
                
        except Exception as e:
            print(f"Error deleting configuration: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """
        Export current configuration to a specific path.
        
        Args:
            export_path: Full path for export
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update last saved timestamp
            self.current_config.last_saved = datetime.now().isoformat()
            
            # Convert to dictionary
            config_dict = self._config_to_dict(self.current_config)
            
            # Save to specified path
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"Configuration exported to: {export_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        Import configuration from a specific path.
        
        Args:
            import_path: Full path to import from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(import_path):
                print(f"Import file not found: {import_path}")
                return False
            
            # Load from file
            with open(import_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # Convert to config object
            self.current_config = self._dict_to_config(config_dict)
            
            print(f"Configuration imported from: {import_path}")
            return True
            
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """Convert AppConfig to dictionary for JSON serialization."""
        return {
            'version': config.version,
            'window_config': asdict(config.window_config),
            'bot_config': asdict(config.bot_config),
            'joystick_config': asdict(config.joystick_config),
            'detection_rules': [asdict(rule) for rule in config.detection_rules],
            'last_saved': config.last_saved
        }
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig object."""
        config = AppConfig()
        
        # Basic fields
        config.version = config_dict.get('version', '1.0.0')
        config.last_saved = config_dict.get('last_saved', '')
        
        # Window config
        window_data = config_dict.get('window_config', {})
        config.window_config = WindowConfig(
            window_title=window_data.get('window_title', 'Xbox'),
            target_width=window_data.get('target_width', 1280),
            target_height=window_data.get('target_height', 720)
        )
        
        # Bot config
        bot_data = config_dict.get('bot_config', {})
        config.bot_config = BotConfig(
            loop_delay=bot_data.get('loop_delay', 0.1),
            action_cooldown=bot_data.get('action_cooldown', 1.0),
            capture_area_width=bot_data.get('capture_area_width', 100),
            capture_area_height=bot_data.get('capture_area_height', 100)
        )
        
        # Joystick config
        joystick_data = config_dict.get('joystick_config', {})
        config.joystick_config = JoystickConfig(
            action_delay=joystick_data.get('action_delay', 1.0),
            auto_focus=joystick_data.get('auto_focus', True)
        )
        
        # Detection rules
        rules_data = config_dict.get('detection_rules', [])
        config.detection_rules = []
        for rule_data in rules_data:
            rule = DetectionRule(
                name=rule_data.get('name', ''),
                template=rule_data.get('template', ''),
                confidence=rule_data.get('confidence', 0.8),
                action=rule_data.get('action', ''),
                enabled=rule_data.get('enabled', True)
            )
            config.detection_rules.append(rule)
        
        return config
    
    # Convenience methods for accessing configuration
    
    def get_window_config(self) -> WindowConfig:
        """Get current window configuration."""
        return self.current_config.window_config
    
    def set_window_config(self, window_title: str, width: int, height: int):
        """Set window configuration."""
        self.current_config.window_config.window_title = window_title
        self.current_config.window_config.target_width = width
        self.current_config.window_config.target_height = height
    
    def get_bot_config(self) -> BotConfig:
        """Get current bot configuration."""
        return self.current_config.bot_config
    
    def set_bot_config(self, loop_delay: float, action_cooldown: float, 
                      capture_width: int, capture_height: int):
        """Set bot configuration."""
        self.current_config.bot_config.loop_delay = loop_delay
        self.current_config.bot_config.action_cooldown = action_cooldown
        self.current_config.bot_config.capture_area_width = capture_width
        self.current_config.bot_config.capture_area_height = capture_height
    
    def get_joystick_config(self) -> JoystickConfig:
        """Get current joystick configuration."""
        return self.current_config.joystick_config
    
    def set_joystick_config(self, action_delay: float, auto_focus: bool):
        """Set joystick configuration."""
        self.current_config.joystick_config.action_delay = action_delay
        self.current_config.joystick_config.auto_focus = auto_focus
    
    def get_detection_rules(self) -> List[DetectionRule]:
        """Get current detection rules."""
        return self.current_config.detection_rules
    
    def add_detection_rule(self, name: str, template: str, confidence: float, action: str, input_mode: str = "controller", enabled: bool = True, 
                          is_cycle_marker: bool = False, cycle_type: str = "none", cycle_name: str = "", 
                          expected_cycle_time: float = 0.0, cycle_tolerance: float = 0.3) -> bool:
        """Add a new detection rule with optional cycle tracking."""
        # Check for duplicate names
        for rule in self.current_config.detection_rules:
            if rule.name == name:
                print(f"DEBUG: Rule with name '{name}' already exists - cannot add")
                return False
        
        rule = DetectionRule(
            name=name,
            template=template,
            confidence=confidence,
            action=action,
            input_mode=input_mode,
            enabled=enabled,
            is_cycle_marker=is_cycle_marker,
            cycle_type=cycle_type,
            cycle_name=cycle_name,
            expected_cycle_time=expected_cycle_time,
            cycle_tolerance=cycle_tolerance
        )
        
        rules_count_before = len(self.current_config.detection_rules)
        self.current_config.detection_rules.append(rule)
        rules_count_after = len(self.current_config.detection_rules)
        
        cycle_info = f" (Cycle: {cycle_name}/{cycle_type})" if is_cycle_marker else ""
        print(f"DEBUG: Added rule '{name}'{cycle_info} - count before: {rules_count_before}, after: {rules_count_after}")
        return True
    
    def remove_detection_rule(self, name: str) -> bool:
        """Remove a detection rule by name."""
        for i, rule in enumerate(self.current_config.detection_rules):
            if rule.name == name:
                del self.current_config.detection_rules[i]
                return True
        return False
    
    def update_detection_rule(self, name: str, template: str, confidence: float, action: str, input_mode: str = "controller", enabled: bool = None) -> bool:
        """Update an existing detection rule."""
        print(f"DEBUG: Attempting to update rule '{name}' - template: {template}, input_mode: {input_mode}")
        
        for i, rule in enumerate(self.current_config.detection_rules):
            if rule.name == name:
                print(f"DEBUG: Found rule '{name}' at index {i} - updating")
                rule.template = template
                rule.confidence = confidence
                rule.action = action
                rule.input_mode = input_mode
                if enabled is not None:
                    rule.enabled = enabled
                return True
        
        print(f"DEBUG: Rule '{name}' not found for update")
        return False
    
    def toggle_rule_enabled(self, name: str) -> bool:
        """Toggle enabled state of a detection rule."""
        for rule in self.current_config.detection_rules:
            if rule.name == name:
                rule.enabled = not rule.enabled
                return True
        return False
    
    def get_rules_for_bot(self) -> List[Dict]:
        """Get detection rules in format expected by BotThread."""
        rules = []
        for rule in self.current_config.detection_rules:
            if rule.enabled:
                rules.append({
                    'name': rule.name,
                    'template': rule.template,
                    'confidence': rule.confidence,
                    'action': rule.action
                })
        return rules
    
    def validate_rule(self, name: str, template: str, confidence: float, action: str) -> Tuple[bool, str]:
        """
        Validate a detection rule before adding/updating.
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Validate name
        if not name or not name.strip():
            return False, "Rule name cannot be empty"
        
        # Check for invalid characters in name
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        if any(char in name for char in invalid_chars):
            return False, f"Rule name contains invalid characters: {', '.join(invalid_chars)}"
        
        # Validate template
        if not template or not template.strip():
            return False, "Template filename cannot be empty"
        
        # Ensure template has .png extension
        if not template.lower().endswith('.png'):
            template += '.png'
        
        # Check if template file exists
        template_path = os.path.join("templates", template)
        if not os.path.exists(template_path):
            return False, f"Template file '{template}' not found in templates folder"
        
        # Validate confidence
        if not (0.0 <= confidence <= 1.0):
            return False, "Confidence must be between 0.0 and 1.0"
        
        # Validate action
        if not action or not action.strip():
            return False, "Action cannot be empty"
        
        # Validate sequence format if it contains commas and colons
        if ',' in action and ':' in action:
            return self._validate_sequence_format(action)
        
        return True, ""
    
    def _validate_sequence_format(self, sequence: str) -> Tuple[bool, str]:
        """Validate sequence format: BUTTON:duration,BUTTON:duration"""
        try:
            steps = sequence.split(',')
            for step in steps:
                step = step.strip()
                if ':' not in step:
                    return False, f"Invalid sequence step format: '{step}'. Expected format: BUTTON:duration"
                
                button, duration_str = step.split(':', 1)
                button = button.strip()
                
                if not button:
                    return False, f"Empty button name in sequence step: '{step}'"
                
                try:
                    duration = float(duration_str.strip())
                    if duration < 0:
                        return False, f"Duration must be positive in step: '{step}'"
                except ValueError:
                    return False, f"Invalid duration in sequence step: '{step}'"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating sequence: {e}"
    
    def get_rule_by_name(self, name: str) -> Optional[DetectionRule]:
        """Get a detection rule by name."""
        for rule in self.current_config.detection_rules:
            if rule.name == name:
                return rule
        return None
    
    def export_rules(self, filepath: str) -> bool:
        """Export detection rules to a JSON file."""
        try:
            rules_data = []
            for rule in self.current_config.detection_rules:
                rules_data.append(asdict(rule))
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "rules_count": len(rules_data),
                "rules": rules_data
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting rules: {e}")
            return False
    
    def import_rules(self, filepath: str, merge: bool = True) -> Tuple[bool, str, int]:
        """
        Import detection rules from a JSON file.
        
        Args:
            filepath: Path to the JSON file to import
            merge: If True, merge with existing rules. If False, replace all rules.
            
        Returns:
            Tuple of (success: bool, message: str, imported_count: int)
        """
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            if 'rules' not in import_data:
                return False, "Invalid import file format: missing 'rules' key", 0
            
            imported_rules = []
            for rule_data in import_data['rules']:
                try:
                    rule = DetectionRule(**rule_data)
                    imported_rules.append(rule)
                except Exception as e:
                    return False, f"Invalid rule data: {e}", 0
            
            # Validate all rules before importing
            for rule in imported_rules:
                is_valid, error = self.validate_rule(rule.name, rule.template, rule.confidence, rule.action)
                if not is_valid:
                    return False, f"Invalid rule '{rule.name}': {error}", 0
            
            # If not merging, clear existing rules
            if not merge:
                self.current_config.detection_rules.clear()
            
            # Add imported rules (skip duplicates if merging)
            added_count = 0
            for rule in imported_rules:
                if merge and any(existing.name == rule.name for existing in self.current_config.detection_rules):
                    continue  # Skip duplicate names when merging
                
                self.current_config.detection_rules.append(rule)
                added_count += 1
            
            return True, f"Successfully imported {added_count} rules", added_count
            
        except Exception as e:
            return False, f"Error importing rules: {e}", 0
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a template file."""
        template_path = os.path.join("templates", template_name)
        if not template_path.endswith('.png'):
            template_path += '.png'
        
        info = {
            "name": template_name,
            "path": template_path,
            "exists": os.path.exists(template_path),
            "size": None,
            "modified": None
        }
        
        if info["exists"]:
            try:
                stat = os.stat(template_path)
                info["size"] = stat.st_size
                info["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception:
                pass
        
        return info
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get comprehensive template statistics for performance monitoring."""
        templates_dir = self.get_templates_dir()
        stats = {
            "total_templates": 0,
            "total_size_bytes": 0,
            "average_size_bytes": 0,
            "largest_template": None,
            "smallest_template": None,
            "templates_without_rules": [],
            "rules_without_templates": [],
            "template_usage_count": {},
            "supported_unlimited": True
        }
        
        if not os.path.exists(templates_dir):
            return stats
        
        try:
            template_files = [f for f in os.listdir(templates_dir) if f.endswith('.png')]
            stats["total_templates"] = len(template_files)
            
            if len(template_files) == 0:
                return stats
            
            # Analyze template files
            sizes = []
            largest_size = 0
            smallest_size = float('inf')
            
            for template_file in template_files:
                template_path = os.path.join(templates_dir, template_file)
                file_size = os.path.getsize(template_path)
                sizes.append(file_size)
                stats["total_size_bytes"] += file_size
                
                if file_size > largest_size:
                    largest_size = file_size
                    stats["largest_template"] = {"name": template_file, "size": file_size}
                
                if file_size < smallest_size:
                    smallest_size = file_size
                    stats["smallest_template"] = {"name": template_file, "size": file_size}
            
            stats["average_size_bytes"] = stats["total_size_bytes"] // len(template_files)
            
            # Analyze template usage
            rules = self.get_detection_rules()
            used_templates = set()
            
            for rule in rules:
                template_name = rule.template
                if not template_name.endswith('.png'):
                    template_name += '.png'
                
                used_templates.add(template_name)
                stats["template_usage_count"][template_name] = stats["template_usage_count"].get(template_name, 0) + 1
            
            # Find unused templates
            all_templates = set(template_files)
            stats["templates_without_rules"] = list(all_templates - used_templates)
            
            # Find rules with missing templates
            for rule in rules:
                template_name = rule.template
                if not template_name.endswith('.png'):
                    template_name += '.png'
                    
                template_path = os.path.join(templates_dir, template_name)
                if not os.path.exists(template_path):
                    stats["rules_without_templates"].append({
                        "rule_name": rule.name,
                        "template_name": template_name
                    })
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    # === CYCLE TRACKING METHODS ===
    
    def start_cycle(self, cycle_name: str, rule_name: str) -> bool:
        """Start a new cycle timing."""
        try:
            import time
            
            # Check if cycle is already active
            for active_cycle in self.current_config.active_cycles:
                if active_cycle.cycle_name == cycle_name and not active_cycle.is_complete:
                    # Cycle already running, ignore duplicate start
                    print(f"DEBUG: Cycle '{cycle_name}' already active, ignoring duplicate start")
                    return False
            
            # Create new cycle tracking
            cycle_data = CycleTrackingData(
                cycle_name=cycle_name,
                start_time=time.time(),
                checkpoints=[{"name": rule_name, "time": time.time()}]
            )
            
            self.current_config.active_cycles.append(cycle_data)
            print(f"DEBUG: Started cycle '{cycle_name}' with rule '{rule_name}'")
            return True
            
        except Exception as e:
            print(f"Error starting cycle: {e}")
            return False
    
    def add_cycle_checkpoint(self, cycle_name: str, checkpoint_name: str) -> bool:
        """Add a checkpoint to an active cycle."""
        try:
            import time
            
            for active_cycle in self.current_config.active_cycles:
                if active_cycle.cycle_name == cycle_name and not active_cycle.is_complete:
                    checkpoint = {"name": checkpoint_name, "time": time.time()}
                    active_cycle.checkpoints.append(checkpoint)
                    print(f"DEBUG: Added checkpoint '{checkpoint_name}' to cycle '{cycle_name}'")
                    return True
            
            print(f"DEBUG: No active cycle '{cycle_name}' found for checkpoint")
            return False
            
        except Exception as e:
            print(f"Error adding checkpoint: {e}")
            return False
    
    def end_cycle(self, cycle_name: str, rule_name: str) -> Dict[str, Any]:
        """End a cycle and calculate statistics."""
        try:
            import time
            current_time = time.time()
            
            for i, active_cycle in enumerate(self.current_config.active_cycles):
                if active_cycle.cycle_name == cycle_name and not active_cycle.is_complete:
                    # Complete the cycle
                    active_cycle.end_time = current_time
                    active_cycle.duration = active_cycle.end_time - active_cycle.start_time
                    active_cycle.is_complete = True
                    active_cycle.checkpoints.append({"name": rule_name, "time": current_time})
                    
                    # Calculate cycle statistics
                    stats = self._calculate_cycle_stats(active_cycle)
                    
                    # Move to completed cycles
                    self.current_config.completed_cycles.append(active_cycle)
                    del self.current_config.active_cycles[i]
                    
                    # Update global statistics
                    self._update_cycle_statistics(cycle_name, stats)
                    
                    print(f"DEBUG: Completed cycle '{cycle_name}' in {active_cycle.duration:.2f}s")
                    return stats
            
            print(f"DEBUG: No active cycle '{cycle_name}' found to end")
            return {}
            
        except Exception as e:
            print(f"Error ending cycle: {e}")
            return {}
    
    def _calculate_cycle_stats(self, cycle_data: CycleTrackingData) -> Dict[str, Any]:
        """Calculate statistics for a completed cycle."""
        stats = {
            "cycle_name": cycle_data.cycle_name,
            "duration": cycle_data.duration,
            "start_time": cycle_data.start_time,
            "end_time": cycle_data.end_time,
            "checkpoint_count": len(cycle_data.checkpoints),
            "checkpoints": cycle_data.checkpoints.copy()
        }
        
        # Calculate checkpoint intervals
        if len(cycle_data.checkpoints) > 1:
            intervals = []
            for i in range(1, len(cycle_data.checkpoints)):
                interval = cycle_data.checkpoints[i]["time"] - cycle_data.checkpoints[i-1]["time"]
                intervals.append({
                    "from": cycle_data.checkpoints[i-1]["name"],
                    "to": cycle_data.checkpoints[i]["name"],
                    "duration": interval
                })
            stats["intervals"] = intervals
        
        return stats
    
    def _update_cycle_statistics(self, cycle_name: str, cycle_stats: Dict[str, Any]):
        """Update global cycle statistics."""
        if cycle_name not in self.current_config.cycle_statistics:
            self.current_config.cycle_statistics[cycle_name] = {
                "total_cycles": 0,
                "total_time": 0.0,
                "average_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
                "last_completed": 0.0
            }
        
        stats = self.current_config.cycle_statistics[cycle_name]
        duration = cycle_stats["duration"]
        
        stats["total_cycles"] += 1
        stats["total_time"] += duration
        stats["average_time"] = stats["total_time"] / stats["total_cycles"]
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)
        stats["last_completed"] = cycle_stats["end_time"]
    
    def get_cycle_statistics(self, cycle_name: str = None) -> Dict[str, Any]:
        """Get cycle statistics."""
        if cycle_name:
            return self.current_config.cycle_statistics.get(cycle_name, {})
        else:
            return self.current_config.cycle_statistics.copy()
    
    def is_cycle_duplicate(self, cycle_name: str, tolerance_seconds: float = 30.0) -> bool:
        """Check if a cycle start might be a duplicate (too soon after last completion)."""
        import time
        current_time = time.time()
        
        # Check if there's already an active cycle
        for active_cycle in self.current_config.active_cycles:
            if active_cycle.cycle_name == cycle_name and not active_cycle.is_complete:
                return True
        
        # Check if last completion was too recent
        if cycle_name in self.current_config.cycle_statistics:
            last_completed = self.current_config.cycle_statistics[cycle_name].get("last_completed", 0)
            if current_time - last_completed < tolerance_seconds:
                return True
        
        return False
    
    def cleanup_old_cycles(self, max_completed_cycles: int = 100):
        """Clean up old completed cycles to prevent memory bloat."""
        if len(self.current_config.completed_cycles) > max_completed_cycles:
            # Keep only the most recent cycles
            self.current_config.completed_cycles = sorted(
                self.current_config.completed_cycles,
                key=lambda x: x.end_time,
                reverse=True
            )[:max_completed_cycles]
            print(f"DEBUG: Cleaned up old cycles, keeping {max_completed_cycles} most recent")


class RulesManager:
    """Manages detection rules with UI integration support."""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
    
    def validate_rule_input(self, name: str, template: str, confidence: float, action: str, input_mode: str = "controller") -> tuple[bool, str]:
        """
        Validate rule input from UI forms.
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Validate input_mode
        valid_modes = ["controller", "keyboard", "mouse"]
        if input_mode not in valid_modes:
            return False, f"Invalid input mode. Must be one of: {', '.join(valid_modes)}"
        
        return self.config_manager.validate_rule(name, template, confidence, action)
    
    def create_rule_from_ui(self, name: str, template: str, confidence: float, action: str, input_mode: str = "controller", enabled: bool = True) -> tuple[bool, str]:
        """
        Create a new rule from UI input with validation.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Validate input
        is_valid, error_msg = self.validate_rule_input(name, template, confidence, action, input_mode)
        if not is_valid:
            return False, error_msg
        
        # Check for duplicate names
        existing_rule = self.config_manager.get_rule_by_name(name)
        if existing_rule:
            return False, f"Rule with name '{name}' already exists"
        
        # Add the rule
        success = self.config_manager.add_detection_rule(name, template, confidence, action, input_mode, enabled)
        if success:
            return True, f"Rule '{name}' created successfully"
        else:
            return False, f"Failed to create rule '{name}'"
    
    def update_rule_from_ui(self, old_name: str, new_name: str, template: str, confidence: float, action: str, input_mode: str = "controller", enabled: bool = True) -> tuple[bool, str]:
        """
        Update an existing rule from UI input with validation.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Validate input
        is_valid, error_msg = self.validate_rule_input(new_name, template, confidence, action, input_mode)
        if not is_valid:
            return False, error_msg
        
        # Handle name change
        if old_name != new_name:
            # Check if new name already exists
            existing_rule = self.config_manager.get_rule_by_name(new_name)
            if existing_rule:
                return False, f"Rule with name '{new_name}' already exists"
            
            # Remove old rule and add new one
            if not self.config_manager.remove_detection_rule(old_name):
                return False, f"Failed to remove old rule '{old_name}'"
            
            success = self.config_manager.add_detection_rule(new_name, template, confidence, action, input_mode, enabled)
            if success:
                return True, f"Rule '{new_name}' updated successfully"
            else:
                return False, f"Failed to update rule '{new_name}'"
        else:
            # Update existing rule
            success = self.config_manager.update_detection_rule(old_name, template, confidence, action, input_mode, enabled)
            if success:
                return True, f"Rule '{new_name}' updated successfully"
            else:
                return False, f"Failed to update rule '{new_name}'"
    
    def get_rules_for_ui(self) -> list[dict]:
        """
        Get rules formatted for UI display.
        
        Returns:
            List of rule dictionaries with UI-friendly format
        """
        rules = self.config_manager.get_detection_rules()
        ui_rules = []
        
        for rule in rules:
            # Check if template exists
            template_path = os.path.join("templates", rule.template)
            if not template_path.endswith('.png'):
                template_path += '.png'
            
            ui_rule = {
                'name': rule.name,
                'template': rule.template,
                'confidence': rule.confidence,
                'action': rule.action,
                'input_mode': getattr(rule, 'input_mode', 'controller'),  # Default for backwards compatibility
                'enabled': rule.enabled,
                'template_exists': os.path.exists(template_path),
                'template_path': template_path
            }
            ui_rules.append(ui_rule)
        
        return ui_rules
    
    def toggle_rule_enabled_by_index(self, rule_index: int) -> tuple[bool, str]:
        """
        Toggle rule enabled state by index.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        rules = self.config_manager.get_detection_rules()
        if 0 <= rule_index < len(rules):
            rule = rules[rule_index]
            success = self.config_manager.toggle_rule_enabled(rule.name)
            if success:
                new_state = "enabled" if not rule.enabled else "disabled"  # State will be toggled
                return True, f"Rule '{rule.name}' {new_state}"
            else:
                return False, f"Failed to toggle rule '{rule.name}'"
        else:
            return False, "Invalid rule index"
    
    def delete_rule_by_index(self, rule_index: int) -> tuple[bool, str]:
        """
        Delete rule by index.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        rules = self.config_manager.get_detection_rules()
        if 0 <= rule_index < len(rules):
            rule = rules[rule_index]
            success = self.config_manager.remove_detection_rule(rule.name)
            if success:
                return True, f"Rule '{rule.name}' deleted successfully"
            else:
                return False, f"Failed to delete rule '{rule.name}'"
        else:
            return False, "Invalid rule index"
    
    def get_rule_by_index(self, rule_index: int) -> Optional[DetectionRule]:
        """Get rule by index."""
        rules = self.config_manager.get_detection_rules()
        if 0 <= rule_index < len(rules):
            return rules[rule_index]
        return None