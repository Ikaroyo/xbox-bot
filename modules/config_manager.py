"""
Configuration Manager Module

Handles saving and loading of bot configuration including rules,
window settings, and other application preferences.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class DetectionRule:
    """Data class for detection rules."""
    name: str
    template: str
    confidence: float
    action: str
    enabled: bool = True


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
class AppConfig:
    """Main application configuration."""
    version: str = "1.0.0"
    window_config: WindowConfig = None
    bot_config: BotConfig = None
    joystick_config: JoystickConfig = None
    detection_rules: List[DetectionRule] = None
    last_saved: str = ""
    
    def __post_init__(self):
        if self.window_config is None:
            self.window_config = WindowConfig()
        if self.bot_config is None:
            self.bot_config = BotConfig()
        if self.joystick_config is None:
            self.joystick_config = JoystickConfig()
        if self.detection_rules is None:
            self.detection_rules = []


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
        
        # Create config directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        self.current_config = AppConfig()
    
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
            
            print(f"Configuration loaded from: {config_path}")
            return True
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
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
    
    def add_detection_rule(self, name: str, template: str, confidence: float, action: str) -> bool:
        """Add a new detection rule."""
        # Check for duplicate names
        for rule in self.current_config.detection_rules:
            if rule.name == name:
                print(f"Rule with name '{name}' already exists")
                return False
        
        rule = DetectionRule(
            name=name,
            template=template,
            confidence=confidence,
            action=action,
            enabled=True
        )
        
        self.current_config.detection_rules.append(rule)
        return True
    
    def remove_detection_rule(self, name: str) -> bool:
        """Remove a detection rule by name."""
        for i, rule in enumerate(self.current_config.detection_rules):
            if rule.name == name:
                del self.current_config.detection_rules[i]
                return True
        return False
    
    def update_detection_rule(self, name: str, template: str, confidence: float, action: str) -> bool:
        """Update an existing detection rule."""
        for rule in self.current_config.detection_rules:
            if rule.name == name:
                rule.template = template
                rule.confidence = confidence
                rule.action = action
                return True
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