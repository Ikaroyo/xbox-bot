"""
Main Stumble Bot Application Window

Combines all tabs and handles main application logic.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os
import json
from typing import Dict, List, Optional, Any

from modules.window_manager import WindowManager
from modules.image_detector import ImageDetector 
from modules.virtual_controller import VirtualController, XboxButton
from modules.bot_thread import BotThread
from modules.config_manager import ConfigManager, AppConfig, DetectionRule

from .run_tab import RunTab
from .configuration_tab import ConfigurationTab
from .joystick_tab import JoystickTab


class StumbleBotMainWindow:
    """Main application window with tabbed interface."""
    
    # Window settings file
    WINDOW_SETTINGS_FILE = "window_settings.json"
    DEFAULT_GEOMETRY = "800x700+100+100"
    
    def __init__(self):
        # Initialize main window
        self.root = ctk.CTk()
        self.root.title("Stumble Bot - Game Automation Tool")
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Load and apply window geometry
        self._load_window_geometry()
        
        # Initialize core modules
        self._init_modules()
        
        # State variables
        self.bot_thread: Optional[BotThread] = None
        self.is_running = False
        self.selected_rule_index: Optional[int] = None
        
        # Create GUI
        self._create_gui()
        
        # Load initial configuration
        self._load_initial_config()
        
        # Setup window close handler to save geometry
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _init_modules(self):
        """Initialize core application modules."""
        try:
            self.window_manager = WindowManager()
            self.image_detector = ImageDetector()
            self.virtual_controller = VirtualController()
            self.config_manager = ConfigManager()
        except Exception as e:
            # For initialization errors, use regular messagebox since window isn't ready
            messagebox.showerror("Initialization Error", f"Failed to initialize modules: {str(e)}")
            self.root.destroy()
            raise
    
    def _create_gui(self):
        """Create the main GUI interface."""
        # Create main notebook for tabs
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.notebook.add("Run")
        self.notebook.add("Configuration")
        self.notebook.add("Joystick")
        
        # Initialize tab classes
        self.run_tab = RunTab(self.notebook.tab("Run"), self)
        self.config_tab = ConfigurationTab(self.notebook.tab("Configuration"), self)
        self.joystick_tab = JoystickTab(self.notebook.tab("Joystick"), self)
        
        # Set default tab
        self.notebook.set("Run")
    
    def _load_window_geometry(self):
        """Load and apply saved window geometry."""
        try:
            if os.path.exists(self.WINDOW_SETTINGS_FILE):
                with open(self.WINDOW_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    geometry = settings.get('geometry', self.DEFAULT_GEOMETRY)
            else:
                geometry = self.DEFAULT_GEOMETRY
            
            self.root.geometry(geometry)
            
            # Ensure window is visible on screen
            self.root.update_idletasks()
            self._ensure_window_on_screen()
            
        except Exception as e:
            print(f"Warning: Could not load window geometry: {e}")
            self.root.geometry(self.DEFAULT_GEOMETRY)
    
    def _save_window_geometry(self):
        """Save current window geometry."""
        try:
            # Get current geometry
            geometry = self.root.geometry()
            
            settings = {
                'geometry': geometry,
                'state': self.root.state()
            }
            
            with open(self.WINDOW_SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save window geometry: {e}")
    
    def _ensure_window_on_screen(self):
        """Ensure window is visible on screen."""
        try:
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Get window dimensions and position
            self.root.update_idletasks()
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            
            # Adjust if window is off-screen
            if x < 0:
                x = 0
            elif x + window_width > screen_width:
                x = screen_width - window_width
            
            if y < 0:
                y = 0
            elif y + window_height > screen_height:
                y = screen_height - window_height
            
            # Apply corrected position
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
        except Exception as e:
            print(f"Warning: Could not ensure window on screen: {e}")
    
    def center_dialog_on_main(self, dialog_window):
        """Center a dialog window on the main application window."""
        try:
            # Update main window to get accurate position/size
            self.root.update_idletasks()
            
            # Get main window position and size
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()
            
            # Update dialog to get its size
            dialog_window.update_idletasks()
            dialog_width = dialog_window.winfo_reqwidth()
            dialog_height = dialog_window.winfo_reqheight()
            
            # Calculate centered position
            center_x = main_x + (main_width - dialog_width) // 2
            center_y = main_y + (main_height - dialog_height) // 2
            
            # Ensure dialog is on screen
            screen_width = dialog_window.winfo_screenwidth()
            screen_height = dialog_window.winfo_screenheight()
            
            if center_x < 0:
                center_x = 0
            elif center_x + dialog_width > screen_width:
                center_x = screen_width - dialog_width
            
            if center_y < 0:
                center_y = 0
            elif center_y + dialog_height > screen_height:
                center_y = screen_height - dialog_height
            
            # Set dialog position
            dialog_window.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")
            
        except Exception as e:
            print(f"Warning: Could not center dialog: {e}")
    
    def show_centered_messagebox(self, title: str, message: str, box_type: str = "info"):
        """Show a messagebox centered on the main window."""
        try:
            # Create a temporary window to center the messagebox
            temp_window = tk.Toplevel(self.root)
            temp_window.withdraw()  # Hide it
            
            # Center the temporary window
            self.center_dialog_on_main(temp_window)
            
            # Show the messagebox relative to the temporary window
            if box_type == "error":
                result = messagebox.showerror(title, message, parent=temp_window)
            elif box_type == "warning":
                result = messagebox.showwarning(title, message, parent=temp_window)
            elif box_type == "question":
                result = messagebox.askyesno(title, message, parent=temp_window)
            else:  # info
                result = messagebox.showinfo(title, message, parent=temp_window)
            
            # Clean up
            temp_window.destroy()
            return result
            
        except Exception as e:
            print(f"Warning: Could not show centered messagebox: {e}")
            # Fallback to regular messagebox
            if box_type == "error":
                return messagebox.showerror(title, message)
            elif box_type == "warning":
                return messagebox.showwarning(title, message)
            elif box_type == "question":
                return messagebox.askyesno(title, message)
            else:
                return messagebox.showinfo(title, message)
    
    def _load_initial_config(self):
        """Load initial configuration and update GUI."""
        try:
            config = self.config_manager.load_configuration()
            self._apply_config_to_gui(config)
        except Exception as e:
            print(f"Warning: Could not load initial configuration: {e}")
            # Continue with default configuration
    
    def _apply_config_to_gui(self, config: AppConfig):
        """Apply configuration to GUI elements."""
        # Window settings
        if hasattr(self.config_tab, 'widgets'):
            widgets = self.config_tab.widgets
            
            if 'window_title_entry' in widgets:
                widgets['window_title_entry'].delete(0, 'end')
                widgets['window_title_entry'].insert(0, config.window_config.window_title)
            
            if 'window_width_entry' in widgets:
                widgets['window_width_entry'].delete(0, 'end')
                widgets['window_width_entry'].insert(0, str(config.window_config.target_width))
            
            if 'window_height_entry' in widgets:
                widgets['window_height_entry'].delete(0, 'end')
                widgets['window_height_entry'].insert(0, str(config.window_config.target_height))
            
            # Bot settings
            if 'loop_delay_entry' in widgets:
                widgets['loop_delay_entry'].delete(0, 'end')
                widgets['loop_delay_entry'].insert(0, str(config.bot_config.loop_delay))
            
            if 'action_cooldown_entry' in widgets:
                widgets['action_cooldown_entry'].delete(0, 'end')
                widgets['action_cooldown_entry'].insert(0, str(config.bot_config.action_cooldown))
        
        # Update rules list
        self._refresh_rules_list()
    
    def _get_current_config(self) -> AppConfig:
        """Get current configuration from GUI."""
        try:
            # Get widgets from config tab
            widgets = self.config_tab.widgets if hasattr(self.config_tab, 'widgets') else {}
            
            # Extract values with defaults
            window_title = widgets.get('window_title_entry', lambda: ctk.CTkEntry(None))().get() or "Xbox"
            
            window_width = 1280
            window_height = 720
            
            if 'window_width_entry' in widgets:
                try:
                    window_width = int(widgets['window_width_entry'].get() or "1280")
                except ValueError:
                    pass
            
            if 'window_height_entry' in widgets:
                try:
                    window_height = int(widgets['window_height_entry'].get() or "720")
                except ValueError:
                    pass
            
            loop_delay = 0.1
            action_cooldown = 1.0
            
            if 'loop_delay_entry' in widgets:
                try:
                    loop_delay = float(widgets['loop_delay_entry'].get() or "0.1")
                except ValueError:
                    pass
            
            if 'action_cooldown_entry' in widgets:
                try:
                    action_cooldown = float(widgets['action_cooldown_entry'].get() or "1.0")
                except ValueError:
                    pass
            
            # Get current config and update values
            current_config = self.config_manager.current_config
            
            # Update window config
            current_config.window_config.window_title = window_title
            current_config.window_config.target_width = window_width
            current_config.window_config.target_height = window_height
            
            # Update bot config
            current_config.bot_config.loop_delay = loop_delay
            current_config.bot_config.action_cooldown = action_cooldown
            
            return current_config
            
        except Exception as e:
            print(f"Error getting current config: {e}")
            return self.config_manager.current_config  # Return current config as fallback
    
    # Bot control methods (called by RunTab)
    def start_bot(self):
        """Start the bot with current configuration."""
        if self.is_running:
            return
        
        try:
            # Get current configuration
            config = self._get_current_config()
            
            # Validate configuration
            if not config.detection_rules:
                self.show_centered_messagebox("Error", "No detection rules configured", "error")
                return
            
            # Update config manager
            self.config_manager.current_config = config
            
            # Create and start bot thread
            self.bot_thread = BotThread(
                window_manager=self.window_manager,
                image_detector=self.image_detector,
                virtual_controller=self.virtual_controller,
                config_manager=self.config_manager
            )
            
            self.bot_thread.start()
            self.is_running = True
            
            # Update UI
            if hasattr(self.run_tab, '_update_bot_status'):
                self.run_tab._update_bot_status()
            
        except Exception as e:
            self.show_centered_messagebox("Start Error", f"Failed to start bot: {str(e)}", "error")
    
    def stop_bot(self):
        """Stop the running bot."""
        if not self.is_running or not self.bot_thread:
            return
        
        try:
            self.bot_thread.stop()
            self.bot_thread.join(timeout=5.0)  # Wait up to 5 seconds
            
            if self.bot_thread.is_alive():
                print("Warning: Bot thread did not stop gracefully")
            
            self.bot_thread = None
            self.is_running = False
            
            # Update UI
            if hasattr(self.run_tab, '_update_bot_status'):
                self.run_tab._update_bot_status()
                
        except Exception as e:
            self.show_centered_messagebox("Stop Error", f"Failed to stop bot: {str(e)}", "error")
    
    def get_bot_stats(self) -> Dict[str, Any]:
        """Get current bot statistics."""
        if self.bot_thread and self.is_running:
            return self.bot_thread.get_stats()
        return {
            'detections': 0,
            'actions': 0,
            'uptime': 0,
            'last_detection': None,
            'last_action': None
        }
    
    # Configuration methods (called by ConfigurationTab)
    def _test_window_detection(self):
        """Test window detection with current settings."""
        try:
            widgets = self.config_tab.widgets
            window_title = widgets.get('window_title_entry', lambda: ctk.CTkEntry(None))().get() or "Xbox"
            
            window = self.window_manager.find_window(window_title)
            if window:
                # Try to focus and resize
                self.window_manager.focus_window(window)
                
                window_width = int(widgets.get('window_width_entry', lambda: ctk.CTkEntry(None))().get() or "1280")
                window_height = int(widgets.get('window_height_entry', lambda: ctk.CTkEntry(None))().get() or "720")
                
                self.window_manager.resize_window(window, window_width, window_height)
                
                self.show_centered_messagebox("Success", f"Window '{window_title}' found and configured!", "info")
            else:
                self.show_centered_messagebox("Not Found", f"Window with title '{window_title}' not found", "warning")
                
        except Exception as e:
            self.show_centered_messagebox("Error", f"Window detection failed: {str(e)}", "error")
    
    def _refresh_rules_list(self):
        """Refresh the rules listbox."""
        if not hasattr(self.config_tab, 'widgets') or 'rules_listbox' not in self.config_tab.widgets:
            return
        
        listbox = self.config_tab.widgets['rules_listbox']
        listbox.delete(0, tk.END)
        
        for i, rule in enumerate(self.config_manager.current_config.detection_rules):
            action_text = rule.action if rule.action_type == "simple" else f"Sequence: {rule.sequence}"
            display_text = f"{rule.name} -> {action_text} (conf: {rule.confidence:.2f})"
            listbox.insert(tk.END, display_text)
    
    def _on_rule_select(self, event):
        """Handle rule selection in listbox."""
        if not hasattr(self.config_tab, 'widgets') or 'rules_listbox' not in self.config_tab.widgets:
            return
        
        listbox = self.config_tab.widgets['rules_listbox']
        selection = listbox.curselection()
        
        if selection:
            self.selected_rule_index = selection[0]
            self._load_rule_to_details(self.selected_rule_index)
    
    def _load_rule_to_details(self, index: int):
        """Load rule data to detail entries."""
        if index < 0 or index >= len(self.config_manager.current_config.detection_rules):
            return
        
        rule = self.config_manager.current_config.detection_rules[index]
        widgets = self.config_tab.widgets
        
        # Clear and set values
        widgets['rule_name_entry'].delete(0, 'end')
        widgets['rule_name_entry'].insert(0, rule.name)
        
        widgets['template_name_entry'].delete(0, 'end')
        widgets['template_name_entry'].insert(0, rule.template_name)
        
        widgets['confidence_slider'].set(rule.confidence)
        widgets['confidence_label'].configure(text=f"{rule.confidence:.2f}")
        
        # Set action type
        if hasattr(self.config_tab, 'action_type_var'):
            self.config_tab.action_type_var.set(rule.action_type)
            self.config_tab._on_action_type_change()
        
        if rule.action_type == "simple":
            widgets['action_combobox'].set(rule.action)
        else:
            widgets['sequence_entry'].delete(0, 'end')
            widgets['sequence_entry'].insert(0, rule.sequence)
    
    def _add_rule(self):
        """Add a new rule."""
        self.selected_rule_index = None
        self._clear_rule_details()
    
    def _edit_rule(self):
        """Edit the selected rule."""
        if self.selected_rule_index is None:
            self.show_centered_messagebox("No Selection", "Please select a rule to edit", "warning")
    
    def _delete_rule(self):
        """Delete the selected rule."""
        if self.selected_rule_index is None:
            self.show_centered_messagebox("No Selection", "Please select a rule to delete", "warning")
            return
        
        if self.show_centered_messagebox("Confirm Delete", "Are you sure you want to delete this rule?", "question"):
            del self.config_manager.current_config.detection_rules[self.selected_rule_index]
            self.selected_rule_index = None
            self._refresh_rules_list()
            self._clear_rule_details()
    
    def _save_rule(self):
        """Save the current rule."""
        try:
            widgets = self.config_tab.widgets
            
            # Get values
            name = widgets['rule_name_entry'].get().strip()
            template_name = widgets['template_name_entry'].get().strip()
            confidence = widgets['confidence_slider'].get()
            
            if not name:
                self.show_centered_messagebox("Error", "Rule name is required", "error")
                return
            
            if not template_name:
                self.show_centered_messagebox("Error", "Template name is required", "error")
                return
            
            # Get action type and values
            action_type = getattr(self.config_tab, 'action_type_var', ctk.StringVar(value="simple")).get()
            
            if action_type == "simple":
                action = widgets['action_combobox'].get()
                sequence = ""
            else:
                action = ""
                sequence = widgets['sequence_entry'].get().strip()
                if not sequence:
                    self.show_centered_messagebox("Error", "Sequence is required for sequence action type", "error")
                    return
            
            # Create rule
            rule = DetectionRule(
                name=name,
                template_name=template_name,
                confidence=confidence,
                action_type=action_type,
                action=action,
                sequence=sequence
            )
            
            # Add or update rule
            if self.selected_rule_index is None:
                self.config_manager.current_config.detection_rules.append(rule)
            else:
                self.config_manager.current_config.detection_rules[self.selected_rule_index] = rule
            
            # Refresh UI
            self._refresh_rules_list()
            self.show_centered_messagebox("Success", "Rule saved successfully", "info")
            
        except Exception as e:
            self.show_centered_messagebox("Error", f"Failed to save rule: {str(e)}", "error")
    
    def _clear_rule_details(self):
        """Clear rule detail entries."""
        widgets = self.config_tab.widgets
        
        widgets['rule_name_entry'].delete(0, 'end')
        widgets['template_name_entry'].delete(0, 'end')
        widgets['confidence_slider'].set(0.8)
        widgets['confidence_label'].configure(text="0.80")
        widgets['action_combobox'].set("A")
        widgets['sequence_entry'].delete(0, 'end')
        
        if hasattr(self.config_tab, 'action_type_var'):
            self.config_tab.action_type_var.set("simple")
            self.config_tab._on_action_type_change()
    
    def _capture_template(self):
        """Capture a template from screen."""
        # This would delegate to capture functionality
        self.show_centered_messagebox("Capture", "Template capture functionality - to be implemented", "info")
    
    def _browse_templates(self):
        """Browse for template files."""
        # This would open file dialog
        self.show_centered_messagebox("Browse", "Template browsing functionality - to be implemented", "info")
    
    def _preview_template(self):
        """Preview selected template."""
        # This would show template preview
        self.show_centered_messagebox("Preview", "Template preview functionality - to be implemented", "info")
    
    def _show_sequence_help(self):
        """Show sequence syntax help."""
        help_text = """
Sequence Syntax Help:

Format: BUTTON:DURATION,BUTTON:DURATION,...

Examples:
• A:0.5 - Press A for 0.5 seconds
• DPAD_UP:2,DPAD_LEFT:1.5 - Press UP for 2s, then LEFT for 1.5s
• LEFT_BUMPER:0.2,A:0.1,RIGHT_TRIGGER:3 - Quick combo

Available Buttons:
A, B, X, Y, DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT,
LEFT_BUMPER, RIGHT_BUMPER, LEFT_TRIGGER, RIGHT_TRIGGER,
LEFT_STICK, RIGHT_STICK, VIEW, MENU, GUIDE

Duration: Time in seconds (decimal allowed)
        """
        self.show_centered_messagebox("Sequence Help", help_text, "info")
    
    def _save_config(self):
        """Save current configuration."""
        try:
            config = self._get_current_config()
            self.config_manager.current_config = config
            self.config_manager.save_config()
            self.show_centered_messagebox("Success", "Configuration saved successfully", "info")
        except Exception as e:
            self.show_centered_messagebox("Error", f"Failed to save configuration: {str(e)}", "error")
    
    def _load_config(self):
        """Load saved configuration."""
        try:
            self.config_manager.load_config()
            config = self.config_manager.current_config
            self._apply_config_to_gui(config)
            self.show_centered_messagebox("Success", "Configuration loaded successfully", "info")
        except Exception as e:
            self.show_centered_messagebox("Error", f"Failed to load configuration: {str(e)}", "error")
    
    def _export_config(self):
        """Export configuration to file."""
        self.show_centered_messagebox("Export", "Configuration export functionality - to be implemented", "info")
    
    def _import_config(self):
        """Import configuration from file."""
        self.show_centered_messagebox("Import", "Configuration import functionality - to be implemented", "info")
    
    def _on_closing(self):
        """Handle application closing."""
        # Save window geometry before closing
        self._save_window_geometry()
        
        if self.is_running:
            if self.show_centered_messagebox("Confirm Exit", "Bot is running. Stop bot and exit?", "question"):
                self.stop_bot()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Start the main application loop."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    try:
        app = StumbleBotMainWindow()
        app.run()
    except Exception as e:
        # Use regular messagebox for fatal errors before window creation
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")


if __name__ == "__main__":
    main()