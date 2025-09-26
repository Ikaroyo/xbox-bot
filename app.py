"""
Main Application GUI

CustomTkinter-based interface with three tabs:
1. Run - Bot control and logging
2. Configuration - Rules and settings
3. Joystick - Manual controller
"""

import customtkinter as ctk
from customtkinter import CTkImage
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import threading
import time
import os
import json
from typing import List, Dict, Optional
import queue
from PIL import Image, ImageTk
try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("Warning: pynput not available. KB2JOY features will be disabled.")

# Windows-specific imports for keyboard suppression
import ctypes
import ctypes.wintypes
try:
    from ctypes import wintypes
    WINDOWS_HOOK_AVAILABLE = True
except ImportError:
    WINDOWS_HOOK_AVAILABLE = False

# Import Windows API for better key suppression
try:
    import win32api
    import win32con
    import win32gui
    WINAPI_AVAILABLE = True
except ImportError:
    WINAPI_AVAILABLE = False

from modules.window_manager import WindowManager
from modules.image_detector import ImageDetector, TemplateManager
from modules.virtual_controller import VirtualController, XboxButton
from modules.bot_thread import BotThread
from modules.config_manager import ConfigManager, RulesManager


class StumbleBotApp:
    """Main application class with GUI and bot management."""
    
    # Window settings file
    WINDOW_SETTINGS_FILE = "window_settings.json"
    DEFAULT_GEOMETRY = "800x600+100+100"
    DEFAULT_TEMPLATE_DIALOG_GEOMETRY = "450x350+150+150"
    
    def __init__(self):
        """Initialize the application."""
        # Initialize modules
        self.window_manager = WindowManager()
        self.image_detector = ImageDetector()
        self.virtual_controller = VirtualController()
        self.config_manager = ConfigManager()
        self.bot_thread = None
        
        # Initialize specialized managers
        self.rules_manager = RulesManager(self.config_manager)
        self.template_manager = TemplateManager(self.image_detector)
        
        # GUI state
        self.log_queue = queue.Queue()
        self.current_rules = []
        self.selected_rule_index = None
        
        # Geometry auto-save variables
        self.geometry_save_timer = None
        self.last_geometry = None
        self.geometry_save_delay = 1000  # 1 second delay before saving
        
        # KB2JOY (Keyboard/Mouse to Joystick) variables
        self.kb2joy_enabled = False
        self.kb2joy_suppress_input = True  # Block original input by default
        self.kb2joy_mappings = {}  # Maps keyboard/mouse inputs to Xbox buttons
        self.kb2joy_listener = None
        self.kb2joy_mouse_listener = None
        self.kb2joy_capture_mode = False
        self.kb2joy_suppress_enabled = True
        self.kb2joy_keys_to_suppress = set()  # Track keys that should be suppressed
        self.kb2joy_suppression_active = False
        self.kb2joy_last_activity = 0
        self.kb2joy_monitor_timer = None
        
        # Windows keyboard hook for proper suppression
        self.kb2joy_hook = None
        self.kb2joy_hook_installed = False
        self.kb2joy_suppressed_keys = set()  # VK codes of keys to suppress
        self.kb2joy_debug_mode = False  # Debug hook behavior
        self.kb2joy_advanced_suppress_var = None  # Will be initialized in GUI setup
        
        # Load default configuration
        self.config_manager.load_config()
        
        # Setup GUI
        self._setup_gui()
        self._load_config_to_gui()
        
        # Start log processing
        self._process_log_queue()
    
    def _setup_gui(self):
        """Setup the main GUI interface."""
        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Main window
        self.root = ctk.CTk()
        self.root.title("Stumble Bot - Game Automation Tool")
        
        # Load and apply window geometry
        self._load_window_geometry()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Create main tab view first, then setup auto-save after everything is ready
        self.tab_view = ctk.CTkTabview(self.root, width=780, height=580)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tab_view.add("Run")
        self.tab_view.add("Configuration")
        self.tab_view.add("Joystick")
        self.tab_view.add("KB2JOY")
        
        # Setup individual tabs
        self._setup_run_tab()
        self._setup_configuration_tab()
        self._setup_joystick_tab()
        self._setup_kb2joy_tab()
        
        # Re-apply saved geometry AFTER all widgets are created
        # This ensures CustomTkinter doesn't override our saved size
        self.root.after(100, self._reapply_saved_geometry)
        
        # Setup auto-save for geometry changes AFTER everything is ready
        # Delay this to allow window to fully initialize
        self.root.after(1000, self._setup_geometry_auto_save)
    
    def _load_window_geometry(self):
        """Load and apply saved window geometry."""
        try:
            if os.path.exists(self.WINDOW_SETTINGS_FILE):
                with open(self.WINDOW_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    geometry = settings.get('geometry', self.DEFAULT_GEOMETRY)
            else:
                geometry = self.DEFAULT_GEOMETRY
            
            # Apply the geometry
            self.root.geometry(geometry)
            
            # Wait a moment for the geometry to take effect
            self.root.update_idletasks()
            
            # Only ensure on screen if geometry was invalid
            self._ensure_window_on_screen_if_needed()
            
        except Exception as e:
            print(f"Warning: Could not load window geometry: {e}")
            self.root.geometry(self.DEFAULT_GEOMETRY)
    
    def _reapply_saved_geometry(self):
        """Re-apply saved geometry after all widgets are created."""
        try:
            if os.path.exists(self.WINDOW_SETTINGS_FILE):
                with open(self.WINDOW_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    saved_geometry = settings.get('geometry', self.DEFAULT_GEOMETRY)
                    
                self.root.geometry(saved_geometry)
                
                # Store this as the baseline for auto-save comparison
                self.last_geometry = saved_geometry
                
        except Exception as e:
            print(f"Warning: Could not re-apply saved geometry: {e}")
    
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
    
    def _ensure_window_on_screen_if_needed(self):
        """Only adjust window position if it's actually off-screen."""
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
            
            # Check if adjustment is actually needed
            needs_adjustment = False
            new_x, new_y = x, y
            
            # Only adjust if completely off-screen or mostly off-screen
            if x + window_width < 50:  # Window is too far left
                new_x = 0
                needs_adjustment = True
            elif x > screen_width - 50:  # Window is too far right
                new_x = screen_width - window_width
                needs_adjustment = True
            
            if y + window_height < 50:  # Window is too far up
                new_y = 0
                needs_adjustment = True
            elif y > screen_height - 50:  # Window is too far down
                new_y = screen_height - window_height
                needs_adjustment = True
            
            if needs_adjustment:
                print(f"DEBUG: Adjusting window position from {x},{y} to {new_x},{new_y}")
                self.root.geometry(f"{window_width}x{window_height}+{new_x}+{new_y}")
                
        except Exception as e:
            print(f"Warning: Could not check window position: {e}")
    
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
    
    def show_centered_filedialog(self, dialog_type: str, **kwargs):
        """Show a file dialog centered on the main window."""
        try:
            # Create a temporary window to parent the file dialog
            temp_window = tk.Toplevel(self.root)
            temp_window.withdraw()  # Hide it
            
            # Center the temporary window
            self.center_dialog_on_main(temp_window)
            
            # Add parent to kwargs
            kwargs['parent'] = temp_window
            
            # Show the appropriate dialog
            if dialog_type == "open":
                result = filedialog.askopenfilename(**kwargs)
            elif dialog_type == "open_multiple":
                result = filedialog.askopenfilenames(**kwargs)
            elif dialog_type == "save":
                result = filedialog.asksaveasfilename(**kwargs)
            else:
                result = None
            
            # Clean up
            temp_window.destroy()
            return result
            
        except Exception as e:
            print(f"Warning: Could not show centered file dialog: {e}")
            # Fallback to regular file dialog without parent
            kwargs.pop('parent', None)  # Remove parent if it was added
            
            if dialog_type == "open":
                return filedialog.askopenfilename(**kwargs)
            elif dialog_type == "open_multiple":
                return filedialog.askopenfilenames(**kwargs)
            elif dialog_type == "save":
                return filedialog.asksaveasfilename(**kwargs)
            else:
                return None
    
    def _setup_geometry_auto_save(self):
        """Setup automatic geometry saving when window changes."""
        # Use the geometry that was set in _reapply_saved_geometry, or get current
        if not self.last_geometry:
            self.root.update_idletasks()
            self.last_geometry = self.root.geometry()
        
        # Bind to window configuration events (resize and move)
        self.root.bind('<Configure>', self._on_window_configure)
        
        # Also bind to window map events (in case of state changes)
        self.root.bind('<Map>', self._on_window_map)
    
    def _on_window_map(self, event):
        """Handle window map events (window becomes visible)."""
        if event.widget == self.root:
            # Small delay to ensure window is properly mapped
            self.root.after(100, self._check_geometry_change)
    
    def _check_geometry_change(self):
        """Check if geometry changed and trigger save if needed."""
        current_geometry = self.root.geometry()
        if current_geometry != self.last_geometry:
            self.last_geometry = current_geometry
            self._schedule_geometry_save()
    
    def _on_window_configure(self, event):
        """Handle window configuration changes (resize, move)."""
        # Only handle events for the main window
        if event.widget == self.root:
            current_geometry = self.root.geometry()
            
            # Check if geometry actually changed
            if current_geometry != self.last_geometry:
                self.last_geometry = current_geometry
                self._schedule_geometry_save()
    
    def _schedule_geometry_save(self):
        """Schedule geometry save with debounce."""
        # Cancel previous timer if exists
        if self.geometry_save_timer:
            self.root.after_cancel(self.geometry_save_timer)
        
        # Schedule save after delay (debounce)
        self.geometry_save_timer = self.root.after(
            self.geometry_save_delay, 
            self._save_geometry_delayed
        )
    
    def _save_geometry_delayed(self):
        """Save geometry after delay (called by timer)."""
        try:
            self._save_window_geometry()
            self.geometry_save_timer = None
            
            # Geometry saved successfully in background
            
        except Exception as e:
            print(f"Warning: Failed to auto-save geometry: {e}")
    
    def _calculate_template_dialog_size(self, available_templates):
        """Calculate optimal dialog size based on template content."""
        try:
            # Base dimensions
            min_width, min_height = 350, 250
            max_width, max_height = 800, 600
            
            # Calculate width based on longest template name
            max_name_length = max(len(template) for template in available_templates) if available_templates else 20
            # Approximate character width in pixels (using Consolas font)
            char_width = 8
            needed_width = max_name_length * char_width + 100  # Add padding for scrollbars and margins
            
            # Calculate height based on number of templates
            template_count = len(available_templates)
            # Each listbox item is approximately 16 pixels high
            needed_height = min(template_count * 16 + 150, 400)  # +150 for headers, buttons, padding
            
            # Apply bounds
            optimal_width = max(min_width, min(needed_width, max_width))
            optimal_height = max(min_height, min(needed_height, max_height))
            
            return f"{optimal_width}x{optimal_height}"
            
        except Exception as e:
            print(f"Warning: Could not calculate dialog size: {e}")
            return "450x350"
    
    def _load_template_dialog_geometry(self, default_size):
        """Load saved template dialog geometry or use calculated default."""
        try:
            if os.path.exists(self.WINDOW_SETTINGS_FILE):
                with open(self.WINDOW_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    dialog_geometry = settings.get('template_dialog_geometry', None)
                    
                    if dialog_geometry:
                        # Parse geometry to validate it
                        if 'x' in dialog_geometry and '+' in dialog_geometry:
                            return dialog_geometry
                    
            # If no saved geometry or invalid, use calculated size with default position
            return f"{default_size}+150+150"
            
        except Exception as e:
            print(f"Warning: Could not load template dialog geometry: {e}")
            return f"{default_size}+150+150"
    
    def _save_template_dialog_geometry(self, dialog_window):
        """Save template dialog geometry to settings."""
        try:
            # Get current geometry
            geometry = dialog_window.geometry()
            
            # Load existing settings
            settings = {}
            if os.path.exists(self.WINDOW_SETTINGS_FILE):
                with open(self.WINDOW_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
            
            # Update template dialog geometry
            settings['template_dialog_geometry'] = geometry
            
            # Save back to file
            with open(self.WINDOW_SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save template dialog geometry: {e}")
    
    def _calculate_preview_dialog_size(self, image_width, image_height):
        """Calculate optimal preview dialog size based on image dimensions."""
        try:
            # Base dimensions for UI elements (header, buttons, padding)
            ui_height = 120
            ui_width = 80
            
            # Maximum display area
            max_display_width = 600
            max_display_height = 400
            
            # Calculate needed size to fit image comfortably
            needed_width = min(image_width + ui_width, max_display_width + ui_width)
            needed_height = min(image_height + ui_height, max_display_height + ui_height)
            
            # Minimum dialog size
            min_width, min_height = 300, 200
            
            # Apply bounds
            optimal_width = max(min_width, needed_width)
            optimal_height = max(min_height, needed_height)
            
            return f"{optimal_width}x{optimal_height}"
            
        except Exception as e:
            print(f"Warning: Could not calculate preview dialog size: {e}")
            return "400x350"
    
    def _load_preview_dialog_geometry(self, default_size):
        """Load saved preview dialog geometry or use calculated default."""
        try:
            if os.path.exists(self.WINDOW_SETTINGS_FILE):
                with open(self.WINDOW_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    dialog_geometry = settings.get('preview_dialog_geometry', None)
                    
                    if dialog_geometry:
                        # Parse geometry to validate it
                        if 'x' in dialog_geometry and '+' in dialog_geometry:
                            return dialog_geometry
                    
            # If no saved geometry or invalid, use calculated size with default position
            return f"{default_size}+200+200"
            
        except Exception as e:
            print(f"Warning: Could not load preview dialog geometry: {e}")
            return f"{default_size}+200+200"
    
    def _save_preview_dialog_geometry(self, dialog_window):
        """Save preview dialog geometry to settings."""
        try:
            # Get current geometry
            geometry = dialog_window.geometry()
            
            # Load existing settings
            settings = {}
            if os.path.exists(self.WINDOW_SETTINGS_FILE):
                with open(self.WINDOW_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
            
            # Update preview dialog geometry
            settings['preview_dialog_geometry'] = geometry
            
            # Save back to file
            with open(self.WINDOW_SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save preview dialog geometry: {e}")
    
    def _setup_run_tab(self):
        """Setup the Run tab with bot control and logging."""
        run_frame = self.tab_view.tab("Run")
        
        # Control section
        control_frame = ctk.CTkFrame(run_frame)
        control_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Start/Stop button
        self.start_stop_btn = ctk.CTkButton(
            control_frame,
            text="Start Bot",
            command=self._toggle_bot,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_stop_btn.pack(side="left", padx=10, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Bot Status: Stopped",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=20, pady=10)
        
        # Debug info button
        debug_btn = ctk.CTkButton(
            control_frame,
            text="Debug Info",
            command=self._show_debug_info,
            width=100
        )
        debug_btn.pack(side="right", padx=(5, 10), pady=10)
        
        # Clear logs button
        clear_btn = ctk.CTkButton(
            control_frame,
            text="Clear Logs",
            command=self._clear_logs,
            width=100
        )
        clear_btn.pack(side="right", padx=10, pady=10)
        
        # Help button
        help_btn = ctk.CTkButton(
            control_frame,
            text="Help",
            command=self._show_help,
            width=80
        )
        help_btn.pack(side="right", padx=(5, 10), pady=10)
        
        # Log section
        log_label = ctk.CTkLabel(run_frame, text="Bot Logs:", font=ctk.CTkFont(size=14, weight="bold"))
        log_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Log text area with scrollbar
        self.log_text = ctk.CTkTextbox(
            run_frame,
            width=750,
            height=400,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Initial log message
        self._add_log("Application initialized. Ready to start bot.")
    
    def _setup_configuration_tab(self):
        """Setup the Configuration tab with rules and settings."""
        config_frame = self.tab_view.tab("Configuration")
        
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(config_frame, width=750, height=550)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Window Configuration Section
        self._setup_window_config_section(scroll_frame)
        
        # Detection Rules Section
        self._setup_detection_rules_section(scroll_frame)
        
        # Bot Settings Section
        self._setup_bot_settings_section(scroll_frame)
        
        # Configuration Management Section
        self._setup_config_management_section(scroll_frame)
    
    def _setup_window_config_section(self, parent):
        """Setup window configuration section."""
        # Window Configuration
        window_frame = ctk.CTkFrame(parent)
        window_frame.pack(fill="x", pady=(0, 10))
        
        window_label = ctk.CTkLabel(window_frame, text="Window Configuration", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        window_label.pack(pady=(10, 5))
        
        # Window title
        title_frame = ctk.CTkFrame(window_frame)
        title_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(title_frame, text="Window Title:", width=120).pack(side="left", padx=5)
        self.window_title_entry = ctk.CTkEntry(title_frame, placeholder_text="Xbox")
        self.window_title_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Window size
        size_frame = ctk.CTkFrame(window_frame)
        size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(size_frame, text="Target Size:", width=120).pack(side="left", padx=5)
        
        self.window_width_entry = ctk.CTkEntry(size_frame, placeholder_text="1280", width=100)
        self.window_width_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(size_frame, text="x").pack(side="left", padx=2)
        
        self.window_height_entry = ctk.CTkEntry(size_frame, placeholder_text="720", width=100)
        self.window_height_entry.pack(side="left", padx=5)
        
        # Test window button
        test_window_btn = ctk.CTkButton(
            window_frame,
            text="Test Window Detection",
            command=self._test_window_detection,
            width=150
        )
        test_window_btn.pack(side="left", pady=10, padx=5)
        
    def _setup_detection_rules_section(self, parent):
        """Setup detection rules management section."""
        # Detection Rules
        rules_frame = ctk.CTkFrame(parent)
        rules_frame.pack(fill="x", pady=(0, 10))
        
        rules_label = ctk.CTkLabel(rules_frame, text="Detection Rules", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        rules_label.pack(pady=(10, 5))
        
        # Rules table and controls
        rules_control_frame = ctk.CTkFrame(rules_frame)
        rules_control_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Rules table container
        table_frame = ctk.CTkFrame(rules_control_frame)
        table_frame.pack(side="left", fill="both", expand=True)
        
        # Create Treeview for rules table
        import tkinter.ttk as ttk
        
        # Style configuration for the treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
        style.configure("Treeview.Heading", background="#404040", foreground="white", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[('selected', '#404040')])
        
        # Create scrollable frame for table
        table_scroll_frame = tk.Frame(table_frame, bg="#2b2b2b")
        table_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Rules table with columns - updated to include input mode
        self.rules_table = ttk.Treeview(table_scroll_frame, columns=('enabled', 'name', 'template', 'input_mode', 'action', 'preview'), show='tree headings', height=15)
        
        # Configure columns
        self.rules_table.column('#0', width=0, stretch=False)  # Hide tree column
        self.rules_table.column('enabled', width=80, anchor='center')
        self.rules_table.column('name', width=120, anchor='w')
        self.rules_table.column('template', width=120, anchor='w')
        self.rules_table.column('input_mode', width=80, anchor='center')
        self.rules_table.column('action', width=100, anchor='w')
        self.rules_table.column('preview', width=60, anchor='center')
        
        # Configure headings
        self.rules_table.heading('enabled', text='Enabled', anchor='center')
        self.rules_table.heading('name', text='Name', anchor='w')
        self.rules_table.heading('template', text='Template', anchor='w')
        self.rules_table.heading('input_mode', text='Input', anchor='center')
        self.rules_table.heading('action', text='Action', anchor='w')
        self.rules_table.heading('preview', text='Preview', anchor='center')
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(table_scroll_frame, orient="vertical", command=self.rules_table.yview)
        h_scrollbar = ttk.Scrollbar(table_scroll_frame, orient="horizontal", command=self.rules_table.xview)
        self.rules_table.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack table and scrollbars
        self.rules_table.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_scroll_frame.grid_rowconfigure(0, weight=1)
        table_scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.rules_table.bind('<<TreeviewSelect>>', self._on_rule_table_select)
        self.rules_table.bind('<Double-1>', self._on_rule_table_double_click)
        
        # Template preview frame
        preview_frame = ctk.CTkFrame(rules_control_frame)
        preview_frame.pack(side="right", fill="y", padx=(10, 0))
        
        preview_label = ctk.CTkLabel(preview_frame, text="Template Preview")
        preview_label.pack(pady=(5, 0))
        
        # Preview image label
        self.preview_image_label = ctk.CTkLabel(
            preview_frame, 
            text="No template\nselected", 
            width=120, 
            height=120,
            fg_color="gray20"
        )
        self.preview_image_label.pack(pady=5, padx=5)
        
        # Rules buttons
        rules_btn_frame = ctk.CTkFrame(rules_control_frame)
        rules_btn_frame.pack(side="right", fill="y", padx=(10, 0))
        
        ctk.CTkButton(rules_btn_frame, text="Add Rule", command=self._add_rule, width=100).pack(pady=2)
        ctk.CTkButton(rules_btn_frame, text="Edit Rule", command=self._edit_rule, width=100).pack(pady=2)
        ctk.CTkButton(rules_btn_frame, text="Delete Rule", command=self._delete_rule, width=100).pack(pady=2)
        ctk.CTkButton(rules_btn_frame, text="Capture Template", command=self._capture_template, width=100).pack(pady=2)
        ctk.CTkButton(rules_btn_frame, text="Import Templates", command=self._import_templates, width=100).pack(pady=2)
        
        # Rule details
        self._setup_rule_details_section(rules_frame)
    
    def _setup_rule_details_section(self, parent):
        """Setup rule details entry section."""
        details_frame = ctk.CTkFrame(parent)
        details_frame.pack(fill="x", padx=10, pady=5)
        
        # Rule name
        name_frame = ctk.CTkFrame(details_frame)
        name_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(name_frame, text="Rule Name:", width=120).pack(side="left", padx=5)
        self.rule_name_entry = ctk.CTkEntry(name_frame, placeholder_text="MainMenu")
        self.rule_name_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Rule enabled checkbox
        self.rule_enabled_var = ctk.BooleanVar(value=True)
        enabled_cb = ctk.CTkCheckBox(name_frame, text="Enabled", variable=self.rule_enabled_var)
        enabled_cb.pack(side="right", padx=5)
        
        # Template name
        template_frame = ctk.CTkFrame(details_frame)
        template_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(template_frame, text="Template:", width=120).pack(side="left", padx=5)
        self.template_name_entry = ctk.CTkEntry(template_frame, placeholder_text="main_menu.png")
        self.template_name_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Template selection and preview buttons
        template_btn_frame = ctk.CTkFrame(template_frame)
        template_btn_frame.pack(side="right", padx=5)
        
        ctk.CTkButton(template_btn_frame, text="Browse", command=self._browse_templates, width=70).pack(side="left", padx=2)
        ctk.CTkButton(template_btn_frame, text="Preview", command=self._preview_template, width=70).pack(side="left", padx=2)
        
        # Confidence slider
        conf_frame = ctk.CTkFrame(details_frame)
        conf_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(conf_frame, text="Confidence:", width=120).pack(side="left", padx=5)
        self.confidence_slider = ctk.CTkSlider(conf_frame, from_=0.0, to=1.0, number_of_steps=30)
        self.confidence_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.confidence_slider.set(0.8)
        
        self.confidence_label = ctk.CTkLabel(conf_frame, text="0.80", width=50)
        self.confidence_label.pack(side="left", padx=5)
        
        self.confidence_slider.configure(command=self._update_confidence_label)
        
        # Input mode selection
        input_mode_frame = ctk.CTkFrame(details_frame)
        input_mode_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(input_mode_frame, text="Input Mode:", width=120).pack(side="left", padx=5)
        self.input_mode_combobox = ctk.CTkComboBox(input_mode_frame, values=["controller", "keyboard", "mouse"])
        self.input_mode_combobox.pack(side="left", fill="x", expand=True, padx=5)
        self.input_mode_combobox.set("controller")
        self.input_mode_combobox.configure(command=self._on_input_mode_change)
        
        # Action combobox and sequence
        action_frame = ctk.CTkFrame(details_frame)
        action_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(action_frame, text="Action:", width=120).pack(side="left", padx=5)
        
        # Action type selector
        self.action_type_var = ctk.StringVar(value="simple")
        action_type_frame = ctk.CTkFrame(action_frame)
        action_type_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        # Radio buttons for action type
        simple_radio = ctk.CTkRadioButton(action_type_frame, text="Simple", 
                                         variable=self.action_type_var, value="simple",
                                         command=self._on_action_type_change)
        simple_radio.pack(side="left", padx=5)
        
        sequence_radio = ctk.CTkRadioButton(action_type_frame, text="Sequence", 
                                          variable=self.action_type_var, value="sequence",
                                          command=self._on_action_type_change)
        sequence_radio.pack(side="left", padx=5)
        
        # Simple action combobox
        self.simple_action_frame = ctk.CTkFrame(details_frame)
        self.simple_action_frame.pack(fill="x", padx=5, pady=2)
        
        self.simple_action_label = ctk.CTkLabel(self.simple_action_frame, text="Button:", width=120)
        self.simple_action_label.pack(side="left", padx=5)
        
        # Controller actions by default
        available_actions = [button.value for button in XboxButton]
        self.action_combobox = ctk.CTkComboBox(self.simple_action_frame, values=available_actions)
        self.action_combobox.pack(side="left", fill="x", expand=True, padx=5)
        self.action_combobox.set("A")
        
        # Sequence action entry
        self.sequence_action_frame = ctk.CTkFrame(details_frame)
        
        ctk.CTkLabel(self.sequence_action_frame, text="Sequence:", width=120).pack(side="left", padx=5)
        self.sequence_entry = ctk.CTkEntry(self.sequence_action_frame, 
                                          placeholder_text="Button:duration,Button:duration (e.g., A:0.1,B:0.2)")
        self.sequence_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Sequence help button
        sequence_help_btn = ctk.CTkButton(self.sequence_action_frame, text="?", 
                                         command=self._show_sequence_help, width=30)
        sequence_help_btn.pack(side="right", padx=5)
        
        # Save rule button
        save_rule_btn = ctk.CTkButton(
            details_frame,
            text="Save Rule",
            command=self._save_rule,
            width=120
        )
        save_rule_btn.pack(pady=10)
    
    def _setup_bot_settings_section(self, parent):
        """Setup bot timing and behavior settings."""
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=(0, 10))
        
        settings_label = ctk.CTkLabel(settings_frame, text="Bot Settings", 
                                     font=ctk.CTkFont(size=16, weight="bold"))
        settings_label.pack(pady=(10, 5))
        
        # Loop delay
        delay_frame = ctk.CTkFrame(settings_frame)
        delay_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(delay_frame, text="Loop Delay (s):", width=120).pack(side="left", padx=5)
        self.loop_delay_entry = ctk.CTkEntry(delay_frame, placeholder_text="0.1", width=100)
        self.loop_delay_entry.pack(side="left", padx=5)
        
        # Action cooldown
        cooldown_frame = ctk.CTkFrame(settings_frame)
        cooldown_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(cooldown_frame, text="Action Cooldown (s):", width=120).pack(side="left", padx=5)
        self.action_cooldown_entry = ctk.CTkEntry(cooldown_frame, placeholder_text="1.0", width=100)
        self.action_cooldown_entry.pack(side="left", padx=5)
        
        # Capture area size
        capture_frame = ctk.CTkFrame(settings_frame)
        capture_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(capture_frame, text="Capture Area:", width=120).pack(side="left", padx=5)
        
        self.capture_width_entry = ctk.CTkEntry(capture_frame, placeholder_text="100", width=80)
        self.capture_width_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(capture_frame, text="x").pack(side="left", padx=2)
        
        self.capture_height_entry = ctk.CTkEntry(capture_frame, placeholder_text="100", width=80)
        self.capture_height_entry.pack(side="left", padx=5)
    
    def _setup_config_management_section(self, parent):
        """Setup configuration save/load section."""
        mgmt_frame = ctk.CTkFrame(parent)
        mgmt_frame.pack(fill="x", pady=(0, 10))
        
        mgmt_label = ctk.CTkLabel(mgmt_frame, text="Configuration Management", 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        mgmt_label.pack(pady=(10, 5))
        
        # Config buttons
        btn_frame = ctk.CTkFrame(mgmt_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btn_frame, text="Save Config", command=self._save_config, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Load Config", command=self._load_config, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Export Config", command=self._export_config, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Import Config", command=self._import_config, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Template Stats", command=self._show_template_stats, width=120).pack(side="left", padx=5)
    
    def _setup_joystick_tab(self):
        """Setup the Joystick tab with manual controls."""
        joystick_frame = self.tab_view.tab("Joystick")
        
        # Create scrollable frame to handle all content
        scroll_frame = ctk.CTkScrollableFrame(joystick_frame, width=750, height=550)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Timer settings
        timer_frame = ctk.CTkFrame(scroll_frame)
        timer_frame.pack(fill="x", padx=10, pady=10)
        
        timer_label = ctk.CTkLabel(timer_frame, text="Action Timer", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        timer_label.pack(pady=(10, 5))
        
        delay_frame = ctk.CTkFrame(timer_frame)
        delay_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(delay_frame, text="Delay (seconds):", width=120).pack(side="left", padx=5)
        self.joystick_delay_entry = ctk.CTkEntry(delay_frame, placeholder_text="1.0", width=100)
        self.joystick_delay_entry.pack(side="left", padx=5)
        self.joystick_delay_entry.insert(0, "1.0")
        
        # Auto-focus checkbox
        self.auto_focus_var = ctk.BooleanVar(value=True)
        auto_focus_cb = ctk.CTkCheckBox(
            timer_frame,
            text="Auto-focus game window",
            variable=self.auto_focus_var
        )
        auto_focus_cb.pack(pady=5)
        
        # Controller buttons
        buttons_frame = ctk.CTkFrame(scroll_frame)
        buttons_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        buttons_label = ctk.CTkLabel(buttons_frame, text="Xbox Controller", 
                                    font=ctk.CTkFont(size=16, weight="bold"))
        buttons_label.pack(pady=(10, 5))
        
        # Create button grid
        self._setup_controller_buttons(buttons_frame)
        
        # Sequence testing section
        sequence_test_frame = ctk.CTkFrame(scroll_frame)
        sequence_test_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        sequence_test_label = ctk.CTkLabel(sequence_test_frame, text="Test Sequence", 
                                          font=ctk.CTkFont(size=14, weight="bold"))
        sequence_test_label.pack(pady=(10, 5))
        
        # Sequence entry
        seq_entry_frame = ctk.CTkFrame(sequence_test_frame)
        seq_entry_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(seq_entry_frame, text="Sequence:", width=80).pack(side="left", padx=5)
        self.test_sequence_entry = ctk.CTkEntry(seq_entry_frame, 
                                               placeholder_text="STICK_UP:2,STICK_LEFT:1,STICK_RIGHT:1")
        self.test_sequence_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        test_seq_btn = ctk.CTkButton(seq_entry_frame, text="Test", 
                                    command=self._test_sequence, width=80)
        test_seq_btn.pack(side="right", padx=5)
        
        # Quick sequence presets
        presets_frame = ctk.CTkFrame(sequence_test_frame)
        presets_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(presets_frame, text="Presets:").pack(side="left", padx=5)
        
        preset_buttons = [
            ("Walk Forward", "STICK_UP:2"),
            ("Circle Movement", "STICK_UP:1,STICK_RIGHT:1,STICK_DOWN:1,STICK_LEFT:1"),
            ("Jump + Move", "A:0.2,STICK_UP:1.5"),
            ("Quick Combo", "X:0.1,Y:0.1,A:0.2")
        ]
        
        for preset_name, preset_sequence in preset_buttons:
            btn = ctk.CTkButton(presets_frame, text=preset_name, width=120,
                               command=lambda seq=preset_sequence: self._load_preset_sequence(seq))
            btn.pack(side="left", padx=2)
    
    def _setup_controller_buttons(self, parent):
        """Setup the virtual controller button grid."""
        # Main buttons (A, B, X, Y)
        main_frame = ctk.CTkFrame(parent)
        main_frame.pack(pady=10)
        
        # Face buttons in Xbox layout
        face_frame = ctk.CTkFrame(main_frame)
        face_frame.pack(side="right", padx=20)
        
        # Y button (top)
        ctk.CTkButton(face_frame, text="Y", command=lambda: self._delayed_button_press("Y"), 
                     width=50, height=50).grid(row=0, column=1, padx=2, pady=2)
        
        # X and B buttons (middle row)
        ctk.CTkButton(face_frame, text="X", command=lambda: self._delayed_button_press("X"), 
                     width=50, height=50).grid(row=1, column=0, padx=2, pady=2)
        ctk.CTkButton(face_frame, text="B", command=lambda: self._delayed_button_press("B"), 
                     width=50, height=50).grid(row=1, column=2, padx=2, pady=2)
        
        # A button (bottom)
        ctk.CTkButton(face_frame, text="A", command=lambda: self._delayed_button_press("A"), 
                     width=50, height=50).grid(row=2, column=1, padx=2, pady=2)
        
        # D-Pad
        dpad_frame = ctk.CTkFrame(main_frame)
        dpad_frame.pack(side="left", padx=20)
        
        ctk.CTkButton(dpad_frame, text="↑", command=lambda: self._delayed_button_press("DPAD_UP"), 
                     width=50, height=50).grid(row=0, column=1, padx=2, pady=2)
        
        ctk.CTkButton(dpad_frame, text="←", command=lambda: self._delayed_button_press("DPAD_LEFT"), 
                     width=50, height=50).grid(row=1, column=0, padx=2, pady=2)
        ctk.CTkButton(dpad_frame, text="→", command=lambda: self._delayed_button_press("DPAD_RIGHT"), 
                     width=50, height=50).grid(row=1, column=2, padx=2, pady=2)
        
        ctk.CTkButton(dpad_frame, text="↓", command=lambda: self._delayed_button_press("DPAD_DOWN"), 
                     width=50, height=50).grid(row=2, column=1, padx=2, pady=2)
        
        # Left Stick Movement
        stick_frame = ctk.CTkFrame(parent)
        stick_frame.pack(pady=10)
        
        stick_label = ctk.CTkLabel(stick_frame, text="Left Stick Movement", 
                                  font=ctk.CTkFont(size=14, weight="bold"))
        stick_label.pack(pady=(5, 10))
        
        # Stick movement grid
        stick_grid_frame = ctk.CTkFrame(stick_frame)
        stick_grid_frame.pack(pady=5)
        
        # Top row: UP-LEFT, UP, UP-RIGHT
        ctk.CTkButton(stick_grid_frame, text="↖", command=lambda: self._delayed_button_press("STICK_UP_LEFT"), 
                     width=60, height=40).grid(row=0, column=0, padx=2, pady=2)
        ctk.CTkButton(stick_grid_frame, text="↑", command=lambda: self._delayed_button_press("STICK_UP"), 
                     width=60, height=40).grid(row=0, column=1, padx=2, pady=2)
        ctk.CTkButton(stick_grid_frame, text="↗", command=lambda: self._delayed_button_press("STICK_UP_RIGHT"), 
                     width=60, height=40).grid(row=0, column=2, padx=2, pady=2)
        
        # Middle row: LEFT, CENTER, RIGHT
        ctk.CTkButton(stick_grid_frame, text="←", command=lambda: self._delayed_button_press("STICK_LEFT"), 
                     width=60, height=40).grid(row=1, column=0, padx=2, pady=2)
        ctk.CTkButton(stick_grid_frame, text="●", command=lambda: self._delayed_button_press("STICK_CENTER"), 
                     width=60, height=40).grid(row=1, column=1, padx=2, pady=2)
        ctk.CTkButton(stick_grid_frame, text="→", command=lambda: self._delayed_button_press("STICK_RIGHT"), 
                     width=60, height=40).grid(row=1, column=2, padx=2, pady=2)
        
        # Bottom row: DOWN-LEFT, DOWN, DOWN-RIGHT
        ctk.CTkButton(stick_grid_frame, text="↙", command=lambda: self._delayed_button_press("STICK_DOWN_LEFT"), 
                     width=60, height=40).grid(row=2, column=0, padx=2, pady=2)
        ctk.CTkButton(stick_grid_frame, text="↓", command=lambda: self._delayed_button_press("STICK_DOWN"), 
                     width=60, height=40).grid(row=2, column=1, padx=2, pady=2)
        ctk.CTkButton(stick_grid_frame, text="↘", command=lambda: self._delayed_button_press("STICK_DOWN_RIGHT"), 
                     width=60, height=40).grid(row=2, column=2, padx=2, pady=2)
        
        # Additional buttons
        extra_frame = ctk.CTkFrame(parent)
        extra_frame.pack(pady=10)
        
        # Shoulder buttons
        shoulder_frame = ctk.CTkFrame(extra_frame)
        shoulder_frame.pack(pady=5)
        
        ctk.CTkButton(shoulder_frame, text="LB", command=lambda: self._delayed_button_press("LB"), 
                     width=80).pack(side="left", padx=10)
        ctk.CTkButton(shoulder_frame, text="RB", command=lambda: self._delayed_button_press("RB"), 
                     width=80).pack(side="left", padx=10)
        
        # Start/Back buttons
        system_frame = ctk.CTkFrame(extra_frame)
        system_frame.pack(pady=5)
        
        ctk.CTkButton(system_frame, text="BACK", command=lambda: self._delayed_button_press("BACK"), 
                     width=80).pack(side="left", padx=10)
        ctk.CTkButton(system_frame, text="START", command=lambda: self._delayed_button_press("START"), 
                     width=80).pack(side="left", padx=10)
    
    def _setup_kb2joy_tab(self):
        """Setup the KB2JOY tab for keyboard/mouse to controller mapping."""
        kb2joy_frame = self.tab_view.tab("KB2JOY")
        
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(kb2joy_frame, width=750, height=550)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header section
        header_frame = ctk.CTkFrame(scroll_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        header_label = ctk.CTkLabel(header_frame, text="KB2JOY - Keyboard/Mouse to Xbox Controller", 
                                   font=ctk.CTkFont(size=18, weight="bold"))
        header_label.pack(pady=(15, 10))
        
        # Check if pynput is available
        if not PYNPUT_AVAILABLE:
            error_frame = ctk.CTkFrame(header_frame)
            error_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            error_label = ctk.CTkLabel(error_frame, 
                                     text="⚠️ pynput library not found. Install with: pip install pynput", 
                                     font=ctk.CTkFont(size=12), 
                                     text_color="orange")
            error_label.pack(pady=10)
            
            install_btn = ctk.CTkButton(error_frame, text="Install pynput", 
                                       command=self._install_pynput, 
                                       width=150)
            install_btn.pack(pady=5)
            
        description_label = ctk.CTkLabel(header_frame, 
                                       text="Convert keyboard and mouse inputs to Xbox controller buttons in real-time", 
                                       font=ctk.CTkFont(size=12), 
                                       text_color="gray")
        description_label.pack(pady=(0, 15))
        
        # Control section
        control_frame = ctk.CTkFrame(scroll_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        control_header = ctk.CTkLabel(control_frame, text="Control", 
                                    font=ctk.CTkFont(size=14, weight="bold"))
        control_header.pack(pady=(10, 5))
        
        # Enable/Disable toggle
        toggle_frame = ctk.CTkFrame(control_frame)
        toggle_frame.pack(fill="x", padx=10, pady=5)
        
        self.kb2joy_enabled_var = ctk.BooleanVar(value=False)
        self.kb2joy_toggle = ctk.CTkSwitch(toggle_frame, 
                                          text="Enable KB2JOY", 
                                          variable=self.kb2joy_enabled_var,
                                          command=self._toggle_kb2joy,
                                          font=ctk.CTkFont(size=12, weight="bold"))
        self.kb2joy_toggle.pack(side="left", padx=10, pady=10)
        
        # Status label
        self.kb2joy_status_label = ctk.CTkLabel(toggle_frame, text="Status: Disabled", 
                                              font=ctk.CTkFont(size=12))
        self.kb2joy_status_label.pack(side="left", padx=20, pady=10)
        
        # Debug button
        debug_btn = ctk.CTkButton(toggle_frame, text="Debug Hook", 
                                 command=self._toggle_kb2joy_debug,
                                 width=100)
        debug_btn.pack(side="right", padx=5, pady=10)
        
        # Clear all mappings button
        clear_btn = ctk.CTkButton(toggle_frame, text="Clear All Mappings", 
                                 command=self._clear_all_mappings,
                                 width=150)
        clear_btn.pack(side="right", padx=10, pady=10)
        
        # Input suppression control
        suppress_frame = ctk.CTkFrame(control_frame)
        suppress_frame.pack(fill="x", padx=10, pady=5)
        
        self.kb2joy_suppress_input_var = ctk.BooleanVar(value=False)
        suppress_checkbox = ctk.CTkCheckBox(suppress_frame,
                                          text="Enable KB2JOY conversion (converts mapped keys to controller)", 
                                          variable=self.kb2joy_suppress_input_var,
                                          font=ctk.CTkFont(size=11))
        suppress_checkbox.pack(side="left", padx=10, pady=5)
        
        suppress_info = ctk.CTkLabel(suppress_frame,
                                   text="Note: Original keyboard input will pass through. Perfect suppression not reliable with current method.",
                                   font=ctk.CTkFont(size=9),
                                   text_color="gray")
        suppress_info.pack(side="left", padx=10, pady=5)
        
        # Advanced suppression option
        advanced_frame = ctk.CTkFrame(control_frame)
        advanced_frame.pack(fill="x", padx=10, pady=5)
        
        self.kb2joy_advanced_suppress_var = ctk.BooleanVar(value=False)
        advanced_checkbox = ctk.CTkCheckBox(advanced_frame,
                                          text="⚠️ Experimental: Attempt input suppression (may cause issues)", 
                                          variable=self.kb2joy_advanced_suppress_var,
                                          font=ctk.CTkFont(size=10))
        advanced_checkbox.pack(side="left", padx=10, pady=5)
        
        advanced_info = ctk.CTkLabel(advanced_frame,
                                   text="Warning: May stop working after first key press. Use at your own risk.",
                                   font=ctk.CTkFont(size=8),
                                   text_color="orange")
        advanced_info.pack(side="left", padx=10, pady=5)
        
        # Mapping section
        mapping_frame = ctk.CTkFrame(scroll_frame)
        mapping_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        mapping_header = ctk.CTkLabel(mapping_frame, text="Input Mappings", 
                                    font=ctk.CTkFont(size=14, weight="bold"))
        mapping_header.pack(pady=(10, 5))
        
        # Instructions
        instructions = ctk.CTkLabel(mapping_frame, 
                                  text="Click 'Capture' next to a controller button, then press the keyboard key or mouse button you want to map to it",
                                  font=ctk.CTkFont(size=10),
                                  text_color="gray",
                                  wraplength=700)
        instructions.pack(pady=(0, 10))
        
        # Create mapping grid
        self._setup_mapping_grid(mapping_frame)
        
        # Save/Load section
        save_load_frame = ctk.CTkFrame(scroll_frame)
        save_load_frame.pack(fill="x", pady=(0, 10))
        
        save_load_header = ctk.CTkLabel(save_load_frame, text="Configuration", 
                                      font=ctk.CTkFont(size=14, weight="bold"))
        save_load_header.pack(pady=(10, 5))
        
        btn_frame = ctk.CTkFrame(save_load_frame)
        btn_frame.pack(pady=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Save Mappings", command=self._save_kb2joy_config, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Load Mappings", command=self._load_kb2joy_config, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Export Config", command=self._export_kb2joy_config, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Import Config", command=self._import_kb2joy_config, width=120).pack(side="left", padx=5)
        
        # Load existing mappings
        self._load_kb2joy_mappings()
    
    def _setup_mapping_grid(self, parent):
        """Setup the mapping grid with all Xbox controller buttons."""
        # Create grid container
        grid_frame = ctk.CTkFrame(parent)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Xbox button categories
        button_categories = {
            "Face Buttons": ["A", "B", "X", "Y"],
            "Shoulder Buttons": ["LB", "RB"],
            "D-Pad": ["DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT"],
            "System": ["START", "BACK"],
            "Thumbsticks": ["LEFT_THUMB", "RIGHT_THUMB"],
            "Left Stick": ["STICK_UP", "STICK_DOWN", "STICK_LEFT", "STICK_RIGHT", 
                          "STICK_UP_LEFT", "STICK_UP_RIGHT", "STICK_DOWN_LEFT", "STICK_DOWN_RIGHT", "STICK_CENTER"]
        }
        
        # Store mapping widgets for updates
        self.mapping_widgets = {}
        
        row = 0
        for category, buttons in button_categories.items():
            # Category header
            category_label = ctk.CTkLabel(grid_frame, text=category, 
                                        font=ctk.CTkFont(size=13, weight="bold"))
            category_label.grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 5))
            row += 1
            
            # Buttons in this category
            for button in buttons:
                # Button name
                btn_label = ctk.CTkLabel(grid_frame, text=button, width=120)
                btn_label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
                
                # Current mapping display
                mapping_label = ctk.CTkLabel(grid_frame, text="Not mapped", 
                                           width=150, 
                                           fg_color="gray20",
                                           corner_radius=5)
                mapping_label.grid(row=row, column=1, padx=5, pady=2)
                
                # Capture button
                capture_btn = ctk.CTkButton(grid_frame, text="Capture", 
                                          command=lambda b=button: self._capture_input_for_button(b),
                                          width=80, height=25)
                capture_btn.grid(row=row, column=2, padx=5, pady=2)
                
                # Clear button
                clear_btn = ctk.CTkButton(grid_frame, text="Clear", 
                                        command=lambda b=button: self._clear_mapping(b),
                                        width=60, height=25,
                                        fg_color="red", hover_color="darkred")
                clear_btn.grid(row=row, column=3, padx=5, pady=2)
                
                # Store widgets for later updates
                self.mapping_widgets[button] = {
                    'label': mapping_label,
                    'capture_btn': capture_btn,
                    'clear_btn': clear_btn
                }
                
                row += 1
    
    # Event handlers and utility methods
    
    def _toggle_bot(self):
        """Toggle bot start/stop state."""
        if self.bot_thread is None or not self.bot_thread.is_running():
            self._start_bot()
        else:
            self._stop_bot()
    
    def _start_bot(self):
        """Start the bot with current configuration."""
        try:
            # Update configuration from GUI
            self._save_gui_to_config()
            
            # Create bot thread
            self.bot_thread = BotThread(
                self.window_manager,
                self.image_detector,
                self.virtual_controller,
                self._add_log,
                self.config_manager  # Add config manager for cycle tracking
            )
            
            # Configure bot
            window_config = self.config_manager.get_window_config()
            bot_config = self.config_manager.get_bot_config()
            
            self.bot_thread.set_window_config(
                window_config.window_title,
                (window_config.target_width, window_config.target_height)
            )
            
            self.bot_thread.set_timing_config(
                bot_config.loop_delay,
                bot_config.action_cooldown
            )
            
            # Get rules and debug
            rules_for_bot = self.config_manager.get_rules_for_bot()
            self._add_log(f"DEBUG: Passing {len(rules_for_bot)} rules to bot thread:")
            for rule in rules_for_bot:
                self._add_log(f"  - {rule['name']}: {rule['template']} -> {rule['action']}")
            
            self.bot_thread.set_rules(rules_for_bot)
            
            # Start bot
            self.bot_thread.start_bot()
            
            # Update GUI
            self.start_stop_btn.configure(text="Stop Bot")
            self.status_label.configure(text="Bot Status: Running")
            
            self._add_log("Bot started successfully")
            
        except Exception as e:
            self._add_log(f"Error starting bot: {e}")
            self.show_centered_messagebox("Error", f"Failed to start bot: {e}", "error")
    
    def _stop_bot(self):
        """Stop the bot."""
        if self.bot_thread:
            self.bot_thread.stop_bot()
            
            # Update GUI
            self.start_stop_btn.configure(text="Start Bot")
            self.status_label.configure(text="Bot Status: Stopped")
            
            self._add_log("Bot stopped")
    
    def _add_log(self, message: str):
        """Add a message to the log queue."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")
    
    def _process_log_queue(self):
        """Process pending log messages and update the GUI."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                
                # Add to text widget
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                
        except queue.Empty:
            pass
        
        # Schedule next update
        self.root.after(100, self._process_log_queue)
    
    def _clear_logs(self):
        """Clear the log text area."""
        self.log_text.delete("1.0", "end")
    
    def _show_debug_info(self):
        """Show debug information about current bot state."""
        try:
            rules = self.config_manager.get_rules_for_bot()
            detection_rules = self.config_manager.get_detection_rules()
            
            debug_info = f"=== DEBUG INFO ===\n"
            debug_info += f"Total rules configured: {len(detection_rules)}\n"
            debug_info += f"Active rules for bot: {len(rules)}\n"
            
            if len(detection_rules) > 0:
                debug_info += f"\nConfigured Rules:\n"
                for rule in detection_rules:
                    status = "✓" if rule.enabled else "✗"
                    template_path = os.path.join("templates", rule.template)
                    template_exists = "EXISTS" if os.path.exists(template_path) else "MISSING"
                    debug_info += f"  {status} {rule.name}: {rule.template} ({template_exists}) -> {rule.action}\n"
            
            # Check templates directory
            templates_dir = "templates"
            if os.path.exists(templates_dir):
                template_files = [f for f in os.listdir(templates_dir) if f.endswith('.png')]
                debug_info += f"\nTemplate Management:\n"
                debug_info += f"Template files found: {len(template_files)}\n"
                debug_info += f"Templates directory: {os.path.abspath(templates_dir)}\n"
                debug_info += f"✅ Unlimited templates supported - add as many as you need!\n"
                
                if len(template_files) > 0:
                    debug_info += f"\nTemplate Files ({len(template_files)} total):\n"
                    for i, template in enumerate(template_files, 1):
                        file_size = os.path.getsize(os.path.join(templates_dir, template))
                        debug_info += f"  {i:3d}. {template} ({file_size} bytes)\n"
                        if i >= 20:  # Show first 20, then summarize
                            remaining = len(template_files) - 20
                            if remaining > 0:
                                debug_info += f"  ... and {remaining} more templates\n"
                            break
            else:
                debug_info += f"\nTemplates directory not found: {templates_dir}\n"
                debug_info += f"💡 Create the templates folder and add your template images\n"
            
            # Bot status
            if self.bot_thread and hasattr(self.bot_thread, 'get_status'):
                status = self.bot_thread.get_status()
                debug_info += f"\nBot Status:\n"
                for key, value in status.items():
                    debug_info += f"  {key}: {value}\n"
                
                # If bot is running, get more detailed info
                if status.get('running', False):
                    debug_info += f"\nBot Thread Details:\n"
                    debug_info += f"  Bot thread alive: {self.bot_thread.is_alive()}\n"
                    debug_info += f"  Actual rules in bot: {len(self.bot_thread.rules) if hasattr(self.bot_thread, 'rules') else 'Unknown'}\n"
            else:
                debug_info += f"\nBot Status: Not created yet\n"
            
            # Controller and input mode info
            debug_info += f"\nController Status:\n"
            debug_info += f"  Connected: {self.virtual_controller.is_connected()}\n"
            
            self._add_log(debug_info)
            
        except Exception as e:
            self._add_log(f"Error generating debug info: {e}")
    
    def _show_help(self):
        """Show help information for troubleshooting."""
        help_text = """
=== TROUBLESHOOTING GUIDE ===

If the bot is not detecting templates:

1. CHECK TEMPLATES:
   - Click "Debug Info" to see if template files exist
   - Templates must be in the 'templates/' folder
   - Use "Capture Template" to create templates
   - NO LIMIT on number of templates - add as many as you need!

2. CHECK RULES:
   - Make sure you have at least one enabled rule
   - Verify template names match actual files
   - Try lowering confidence threshold (0.7-0.8)
   - NO LIMIT on number of rules - create unlimited detection rules!

3. CHECK WINDOW:
   - Use "Test Window Detection" to verify target window
   - Use "Test Background Input" to verify input injection works
   - Make sure window title is exactly correct
   - Window should be visible and not minimized
   - If background input fails, try focusing the window first

4. TESTING:
   - Use the test template: run 'python create_test_template.py'
   - Display the test image on screen and start bot
   - Check logs for "Template not found" messages

5. JOYSTICK TESTING:
   - Use Joystick tab to test controller simulation
   - If joystick works but bot doesn't, it's a detection issue

6. COMMON ISSUES:
   - Game graphics settings changed = recapture templates
   - Multiple windows with same name = check Debug Info
   - Anti-cheat software may block virtual controller
   
7. PERFORMANCE:
   - Increase Loop Delay if CPU usage is high
   - Smaller templates = faster detection
   - Avoid overlapping elements in templates

8. BACKGROUND INPUT:
   - Enable "Background input" in Bot Settings to control game without focusing
   - Uses keyboard simulation to send controller input directly to target window
   - Button mapping: A=Space, B=X, Arrows=D-Pad, WASD=Analog stick movement
   - Works with games that accept keyboard input when not focused
   - Allows you to work in other applications while bot runs

Click "Debug Info" for current status information.
"""
        self._add_log(help_text)
    
    def _update_confidence_label(self, value):
        """Update confidence slider label."""
        self.confidence_label.configure(text=f"{value:.2f}")
    
    def _on_rule_table_select(self, event):
        """Handle rule selection in table."""
        selection = self.rules_table.selection()
        if selection:
            item = selection[0]
            # Get the rule index from the item text
            rule_index_text = self.rules_table.item(item, 'text')
            if rule_index_text.isdigit():
                rule_index = int(rule_index_text)
                if 0 <= rule_index < len(self.current_rules):
                    self.selected_rule_index = rule_index
                    self._load_rule_to_details(rule_index)
                    self._update_template_preview(rule_index)
                    self._add_log(f"Selected rule {rule_index + 1}: '{self.current_rules[rule_index].name}'")
                else:
                    self._add_log(f"Invalid rule index: {rule_index}")
                    self.selected_rule_index = None
        else:
            # No selection - clear state
            self.selected_rule_index = None
            self._clear_preview_image("No rule\nselected")
    
    def _on_rule_table_double_click(self, event):
        """Handle double-click on table rows to toggle enabled state or show preview."""
        item = self.rules_table.identify('item', event.x, event.y)
        column = self.rules_table.identify('column', event.x, event.y)
        
        if item:
            # Get rule index from item text
            rule_index_text = self.rules_table.item(item, 'text')
            if rule_index_text.isdigit():
                rule_index = int(rule_index_text)
                
                if column == '#1':  # Enabled column
                    self._toggle_rule_enabled(rule_index)
                elif column == '#5':  # Preview column
                    self._show_template_preview_popup(rule_index)
                else:
                    # Edit rule on double-click anywhere else
                    self.selected_rule_index = rule_index
                    self._load_rule_to_details(rule_index)
                    self._edit_rule()
    
    def _clear_preview_image(self, text: str = "No template\nselected", fg_color: str = "gray20"):
        """Helper method to safely clear the preview image."""
        try:
            self.preview_image_label.configure(
                image="",
                text=text,
                fg_color=fg_color
            )
            # Clear image reference
            if hasattr(self.preview_image_label, '_current_image'):
                delattr(self.preview_image_label, '_current_image')
        except Exception as e:
            print(f"Error clearing preview image: {e}")
    
    def _update_template_preview(self, rule_index: int):
        """Update the template preview image."""
        try:
            if 0 <= rule_index < len(self.current_rules):
                rule = self.current_rules[rule_index]
                template_path = os.path.join("templates", rule.template)
                
                # Ensure .png extension
                if not template_path.endswith('.png'):
                    template_path += '.png'
                
                if os.path.exists(template_path):
                    # Load and resize image for preview
                    img = Image.open(template_path)
                    
                    # Calculate size maintaining aspect ratio
                    max_size = 100
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Convert to CTkImage for proper scaling
                    ctk_image = CTkImage(light_image=img, dark_image=img, size=img.size)
                    
                    # Clear any existing image first
                    self.preview_image_label.configure(image="", text="")
                    
                    # Update the preview label with new image
                    self.preview_image_label.configure(
                        image=ctk_image, 
                        text=""
                    )
                    # Keep a strong reference to prevent garbage collection
                    self.preview_image_label._current_image = ctk_image
                else:
                    # Template file not found
                    self.preview_image_label.configure(
                        image="",
                        text=f"Template\n'{rule.template}'\nnot found",
                        fg_color="red"
                    )
                    # Clear image reference
                    if hasattr(self.preview_image_label, '_current_image'):
                        delattr(self.preview_image_label, '_current_image')
            else:
                # No rule selected
                self.preview_image_label.configure(
                    image="",
                    text="No template\nselected",
                    fg_color="gray20"
                )
                # Clear image reference
                if hasattr(self.preview_image_label, '_current_image'):
                    delattr(self.preview_image_label, '_current_image')
                
        except Exception as e:
            # Error loading image
            self.preview_image_label.configure(
                image="",
                text=f"Error loading\ntemplate:\n{str(e)[:20]}...",
                fg_color="red"
            )
            # Clear image reference
            if hasattr(self.preview_image_label, '_current_image'):
                delattr(self.preview_image_label, '_current_image')
    
    def _load_rule_to_details(self, index: int):
        """Load selected rule data to detail entries."""
        if 0 <= index < len(self.current_rules):
            rule = self.current_rules[index]
            
            self.rule_name_entry.delete(0, "end")
            self.rule_name_entry.insert(0, rule.name)
            
            self.template_name_entry.delete(0, "end")
            self.template_name_entry.insert(0, rule.template)
            
            self.confidence_slider.set(rule.confidence)
            
            # Set enabled state
            self.rule_enabled_var.set(rule.enabled)
            
            # Set input mode (default to controller for backwards compatibility)
            input_mode = getattr(rule, 'input_mode', 'controller')
            self.input_mode_combobox.set(input_mode)
            
            # Update action interface based on input mode
            self._on_input_mode_change()
            
            # Check if action is a sequence or simple action
            action = rule.action
            if ',' in action and ':' in action:
                # It's a sequence
                self.action_type_var.set("sequence")
                self.sequence_entry.delete(0, "end")
                self.sequence_entry.insert(0, action)
            else:
                # It's a simple action
                self.action_type_var.set("simple")
                self.action_combobox.set(action)
            
            # Update UI based on action type
            self._on_action_type_change()
    
    def _delayed_button_press(self, button_name: str):
        """Execute button press with delay and auto-focus."""
        def execute_delayed():
            try:
                delay = float(self.joystick_delay_entry.get())
                
                self._add_log(f"Joystick action scheduled: {button_name} in {delay}s")
                
                # Wait for delay
                time.sleep(delay)
                
                # Auto-focus if enabled
                if self.auto_focus_var.get():
                    window_title = self.window_title_entry.get() or "Xbox"
                    window = self.window_manager.select_window(window_title)
                    if window:
                        self.window_manager.focus_window(window)
                        time.sleep(0.1)  # Give window time to focus
                        self._add_log(f"Focused window: {window['title']}")
                
                # Execute button press
                button = self.virtual_controller.get_button_from_string(button_name)
                if button:
                    success = self.virtual_controller.press_button(button)
                    if success:
                        self._add_log(f"Joystick action executed: {button_name}")
                        
                        # Wait additional time to let user observe the reaction
                        self._add_log(f"Waiting {delay}s to observe target window reaction...")
                        time.sleep(delay)
                        self._add_log(f"Joystick action complete: {button_name}")
                    else:
                        self._add_log(f"Failed to execute joystick action: {button_name}")
                else:
                    self._add_log(f"Unknown button: {button_name}")
                    
            except ValueError:
                self._add_log("Invalid delay value in joystick settings")
            except Exception as e:
                self._add_log(f"Error in delayed button press: {e}")
        
        # Execute in background thread
        threading.Thread(target=execute_delayed, daemon=True).start()
    
    def _test_sequence(self):
        """Test a sequence from the joystick tab."""
        def execute_sequence():
            try:
                delay = float(self.joystick_delay_entry.get())
                sequence = self.test_sequence_entry.get().strip()
                
                if not sequence:
                    self._add_log("No sequence entered to test")
                    return
                
                self._add_log(f"Testing sequence in {delay}s: {sequence}")
                
                # Wait for delay
                time.sleep(delay)
                
                # Auto-focus if enabled
                if self.auto_focus_var.get():
                    window_title = self.window_title_entry.get() or "Xbox"
                    window = self.window_manager.select_window(window_title)
                    if window:
                        self.window_manager.focus_window(window)
                        time.sleep(0.1)  # Give window time to focus
                        self._add_log(f"Focused window: {window['title']}")
                
                # Execute sequence
                success = self.virtual_controller.execute_sequence(sequence)
                if success:
                    self._add_log(f"Sequence executed successfully: {sequence}")
                    
                    # Wait additional time to let user observe the reaction
                    self._add_log(f"Waiting {delay}s to observe target window reaction...")
                    time.sleep(delay)
                    self._add_log(f"Sequence test complete: {sequence}")
                else:
                    self._add_log(f"Failed to execute sequence: {sequence}")
                    
            except ValueError:
                self._add_log("Invalid delay value in joystick settings")
            except Exception as e:
                self._add_log(f"Error in sequence test: {e}")
        
        # Execute in background thread
        threading.Thread(target=execute_sequence, daemon=True).start()
    
    def _load_preset_sequence(self, sequence: str):
        """Load a preset sequence into the test field."""
        self.test_sequence_entry.delete(0, "end")
        self.test_sequence_entry.insert(0, sequence)
        self._add_log(f"Loaded preset sequence: {sequence}")
    
    def _test_window_detection(self):
        """Test window detection with current settings."""
        try:
            window_title = self.window_title_entry.get() or "Xbox"
            windows = self.window_manager.find_windows_by_title(window_title)
            
            if not windows:
                self._add_log(f"No windows found with title '{window_title}'")
                self.show_centered_messagebox("Window Detection", f"No windows found with title '{window_title}'", "info")
            elif len(windows) == 1:
                window = windows[0]
                self._add_log(f"Window found: {window['process_name']} (PID: {window['pid']})")
                messagebox.showinfo("Window Detection", 
                                  f"Window found:\nProcess: {window['process_name']}\nPID: {window['pid']}")
            else:
                info = f"Multiple windows found with title '{window_title}':\n"
                for i, window in enumerate(windows):
                    info += f"{i+1}. {window['process_name']} (PID: {window['pid']})\n"
                    self._add_log(f"Window {i+1}: {window['process_name']} (PID: {window['pid']})")
                
                messagebox.showinfo("Window Detection", info)
                
        except Exception as e:
            self._add_log(f"Error testing window detection: {e}")
            messagebox.showerror("Error", f"Window detection failed: {e}")
    
    # Configuration methods (placeholder implementations)
    
    def _load_config_to_gui(self):
        """Load current configuration to GUI elements."""
        try:
            window_config = self.config_manager.get_window_config()
            bot_config = self.config_manager.get_bot_config()
            joystick_config = self.config_manager.get_joystick_config()
            
            # Window config
            self.window_title_entry.insert(0, window_config.window_title)
            self.window_width_entry.insert(0, str(window_config.target_width))
            self.window_height_entry.insert(0, str(window_config.target_height))
            
            # Bot config
            self.loop_delay_entry.insert(0, str(bot_config.loop_delay))
            self.action_cooldown_entry.insert(0, str(bot_config.action_cooldown))
            self.capture_width_entry.insert(0, str(bot_config.capture_area_width))
            self.capture_height_entry.insert(0, str(bot_config.capture_area_height))
            
            # Joystick config
            self.joystick_delay_entry.delete(0, "end")
            self.joystick_delay_entry.insert(0, str(joystick_config.action_delay))
            self.auto_focus_var.set(joystick_config.auto_focus)
            
            # Load rules
            self._refresh_rules_list()
            
        except Exception as e:
            self._add_log(f"Error loading configuration to GUI: {e}")
    
    def _save_gui_to_config(self):
        """Save GUI settings to configuration."""
        try:
            # Window config
            window_title = self.window_title_entry.get() or "Xbox"
            width = int(self.window_width_entry.get() or "1280")
            height = int(self.window_height_entry.get() or "720")
            self.config_manager.set_window_config(window_title, width, height)
            
            # Bot config
            loop_delay = float(self.loop_delay_entry.get() or "0.1")
            action_cooldown = float(self.action_cooldown_entry.get() or "1.0")
            capture_width = int(self.capture_width_entry.get() or "100")
            capture_height = int(self.capture_height_entry.get() or "100")
            self.config_manager.set_bot_config(loop_delay, action_cooldown, capture_width, capture_height)
            
            # Joystick config
            joystick_delay = float(self.joystick_delay_entry.get() or "1.0")
            auto_focus = self.auto_focus_var.get()
            self.config_manager.set_joystick_config(joystick_delay, auto_focus)
            
        except ValueError as e:
            self._add_log(f"Invalid value in configuration: {e}")
            raise
        except Exception as e:
            self._add_log(f"Error saving GUI to configuration: {e}")
            raise
    
    def _refresh_rules_list(self):
        """Refresh the rules table with performance optimizations for large rule sets."""
        # Clear existing items
        for item in self.rules_table.get_children():
            self.rules_table.delete(item)
            
        self.current_rules = self.config_manager.get_detection_rules()
        
        # Batch insert for better performance with large rule sets
        items_to_insert = []
        
        for i, rule in enumerate(self.current_rules):
            # State indicator
            enabled_text = "✓ Enabled" if rule.enabled else "✗ Disabled"
            
            # Check if template exists for preview (cached check for performance)
            template_path = os.path.join("templates", rule.template)
            if not template_path.endswith('.png'):
                template_path += '.png'
            preview_text = "📷" if os.path.exists(template_path) else "❌"
            
            # Get input mode (default to "controller" for backwards compatibility)
            input_mode = getattr(rule, 'input_mode', 'controller')
            input_mode_display = input_mode.title()  # Capitalize first letter
            
            # Prepare item data
            items_to_insert.append((str(i), (
                enabled_text,
                rule.name,
                rule.template,
                input_mode_display,
                rule.action,
                preview_text
            )))
        
        # Batch insert all items
        for item_text, values in items_to_insert:
            self.rules_table.insert('', 'end', text=item_text, values=values)
        
        # Update status message
        rule_count = len(self.current_rules)
        if hasattr(self, 'status_label'):
            status_text = f"Bot Status: Stopped | {rule_count} rules configured"
            if rule_count > 100:
                status_text += " | ⚡ Optimized for large rule sets"
            # Note: Don't update if bot is running to avoid overriding running status
            current_status = self.status_label.cget("text")
            if "Running" not in current_status:
                self.status_label.configure(text=status_text)
        
        # Clear template preview
        if hasattr(self, 'preview_image_label'):
            self._clear_preview_image("No template\\nselected")
            
        # Clear selection
        self.selected_rule_index = None
        
        # Log performance info for large datasets
        if rule_count > 50:
            self._add_log(f"📊 Performance: Loaded {rule_count} rules successfully")
            if rule_count > 200:
                self._add_log("💡 Tip: Consider grouping similar rules or using more specific templates for better performance")
    
    # Rules management methods
    def _add_rule(self):
        """Add a new detection rule."""
        try:
            # Clear detail entries for new rule
            self.rule_name_entry.delete(0, "end")
            self.template_name_entry.delete(0, "end")
            self.confidence_slider.set(0.8)
            
            # Reset input mode to default
            self.input_mode_combobox.set("controller")
            self._on_input_mode_change()  # Update available actions
            
            # Reset action type to simple
            self.action_type_var.set("simple")
            self._on_action_type_change()
            
            # Set default action based on input mode
            self.action_combobox.set("A")
            
            # Reset enabled state
            self.rule_enabled_var.set(True)
            
            # CRITICAL: Clear selection to ensure new rule creation
            self.selected_rule_index = None
            
            # Clear table selection
            if hasattr(self, 'rules_table'):
                self.rules_table.selection_remove(self.rules_table.selection())
            
            # Clear template preview
            self._clear_preview_image("Ready for new\ntemplate")
            
            self._add_log("🆕 Ready to add NEW rule - fill in details and click Save Rule")
            self._add_log(f"DEBUG: Cleared selection (selected_rule_index = {self.selected_rule_index})")
            
        except Exception as e:
            self._add_log(f"Error preparing new rule: {e}")
    
    def _edit_rule(self):
        """Edit the selected rule."""
        try:
            if self.selected_rule_index is None:
                messagebox.showwarning("No Selection", "Please select a rule to edit")
                return
            
            # Rule data is already loaded in detail entries from selection
            self._add_log(f"Editing rule at index {self.selected_rule_index}")
            
        except Exception as e:
            self._add_log(f"Error editing rule: {e}")
    
    def _delete_rule(self):
        """Delete the selected rule."""
        try:
            if self.selected_rule_index is None:
                messagebox.showwarning("No Selection", "Please select a rule to delete")
                return
            
            rule = self.current_rules[self.selected_rule_index]
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", f"Delete rule '{rule.name}'?"):
                # Remove from config
                if self.config_manager.remove_detection_rule(rule.name):
                    self._add_log(f"Rule '{rule.name}' deleted")
                    
                    # Refresh GUI
                    self._refresh_rules_list()
                    
                    # Clear details
                    self.rule_name_entry.delete(0, "end")
                    self.template_name_entry.delete(0, "end")
                    self.confidence_slider.set(0.8)
                    self.action_combobox.set("A")
                    
                    self.selected_rule_index = None
                else:
                    self._add_log(f"Failed to delete rule '{rule.name}'")
                    
        except Exception as e:
            self._add_log(f"Error deleting rule: {e}")
    
    def _save_rule(self):
        """Save the current rule details."""
        try:
            # Get values from GUI
            name = self.rule_name_entry.get().strip()
            template = self.template_name_entry.get().strip()
            confidence = self.confidence_slider.get()
            input_mode = self.input_mode_combobox.get()
            
            # Get action based on type
            action_type = self.action_type_var.get()
            if action_type == "simple":
                action = self.action_combobox.get()
            else:  # sequence
                action = self.sequence_entry.get().strip()
            
            # Get enabled state
            enabled = self.rule_enabled_var.get()
            
            # Validate inputs
            if not name:
                messagebox.showerror("Invalid Input", "Rule name is required")
                return
            
            if not template:
                messagebox.showerror("Invalid Input", "Template name is required")
                return
            
            if not action:
                messagebox.showerror("Invalid Input", "Action is required")
                return
            
            if input_mode not in ["controller", "keyboard", "mouse"]:
                messagebox.showerror("Invalid Input", "Invalid input mode selected")
                return
            
            # Validate sequence format if it's a sequence
            if action_type == "sequence":
                if not self._validate_sequence(action, input_mode):
                    return
            
            # Check if template file exists
            template_path = os.path.join("templates", template)
            if not template.endswith('.png'):
                template += '.png'
                template_path = os.path.join("templates", template)
            
            if not os.path.exists(template_path):
                if not messagebox.askyesno("Template Missing", 
                                         f"Template file '{template}' not found. Save rule anyway?"):
                    return
            
            # Determine if this is an update or new rule
            if self.selected_rule_index is not None and 0 <= self.selected_rule_index < len(self.current_rules):
                # Update existing rule
                old_rule = self.current_rules[self.selected_rule_index]
                self._add_log(f"Updating existing rule at index {self.selected_rule_index}: '{old_rule.name}'")
                
                if self.config_manager.update_detection_rule(old_rule.name, template, confidence, action, input_mode, enabled):
                    # If name changed, we need to remove old and add new
                    if old_rule.name != name:
                        self.config_manager.remove_detection_rule(old_rule.name)
                        self.config_manager.add_detection_rule(name, template, confidence, action, input_mode, enabled)
                    
                    self._add_log(f"Rule '{name}' updated successfully")
                else:
                    self._add_log(f"Failed to update rule '{name}'")
            else:
                # Add new rule
                self._add_log(f"Adding new rule: '{name}' (selected_rule_index = {self.selected_rule_index})")
                
                if self.config_manager.add_detection_rule(name, template, confidence, action, input_mode, enabled):
                    self._add_log(f"Rule '{name}' added successfully")
                else:
                    self._add_log(f"Failed to add rule '{name}' (name may already exist)")
                    messagebox.showerror("Error", f"Failed to add rule. Rule name '{name}' may already exist.")
                    return
            
            # Refresh GUI
            self._refresh_rules_list()
            
            # Clear selection and form for next rule
            self.selected_rule_index = None
            
            # Clear the form fields to prepare for next rule
            self.rule_name_entry.delete(0, "end")
            self.template_name_entry.delete(0, "end")
            self.confidence_slider.set(0.8)
            self.input_mode_combobox.set("controller")
            self._on_input_mode_change()
            self.action_type_var.set("simple")
            self._on_action_type_change()
            self.action_combobox.set("A")
            self.rule_enabled_var.set(True)
            
        except Exception as e:
            self._add_log(f"Error saving rule: {e}")
            messagebox.showerror("Error", f"Failed to save rule: {e}")
    
    def _validate_sequence(self, sequence: str, input_mode: str = "controller") -> bool:
        """Validate sequence format based on input mode."""
        try:
            if not sequence.strip():
                messagebox.showerror("Invalid Sequence", "Sequence cannot be empty")
                return False
            
            steps = sequence.split(',')
            
            if input_mode == "controller":
                return self._validate_controller_sequence(steps)
            elif input_mode == "keyboard":
                return self._validate_keyboard_sequence(steps)
            elif input_mode == "mouse":
                return self._validate_mouse_sequence(steps)
            else:
                messagebox.showerror("Invalid Input Mode", f"Unknown input mode: {input_mode}")
                return False
                
        except Exception as e:
            messagebox.showerror("Validation Error", f"Error validating sequence: {e}")
            return False
    
    def _validate_controller_sequence(self, steps: list) -> bool:
        """Validate controller sequence format."""
        available_buttons = [button.value for button in XboxButton]
        
        for step in steps:
            step = step.strip()
            if ':' not in step:
                messagebox.showerror("Invalid Sequence", 
                                   f"Invalid step format: '{step}'. Use BUTTON:duration format.")
                return False
            
            button_name, duration_str = step.split(':', 1)
            button_name = button_name.strip()
            duration_str = duration_str.strip()
            
            # Validate button name
            if button_name not in available_buttons:
                messagebox.showerror("Invalid Sequence", 
                                   f"Unknown button: '{button_name}'. Available: {', '.join(available_buttons)}")
                return False
            
            # Validate duration
            try:
                duration = float(duration_str)
                if duration <= 0 or duration > 10:
                    messagebox.showerror("Invalid Sequence", 
                                       f"Duration must be between 0 and 10 seconds: '{duration_str}'")
                    return False
            except ValueError:
                messagebox.showerror("Invalid Sequence", 
                                   f"Invalid duration: '{duration_str}'. Must be a number.")
                return False
        
        return True
    
    def _validate_keyboard_sequence(self, steps: list) -> bool:
        """Validate keyboard sequence format."""
        from modules.virtual_controller import KeyboardKey
        available_keys = [key.value for key in KeyboardKey]
        
        for step in steps:
            step = step.strip()
            if ':' not in step:
                messagebox.showerror("Invalid Sequence", 
                                   f"Invalid step format: '{step}'. Use KEY:duration or KEY1+KEY2:duration format.")
                return False
            
            key_part, duration_str = step.split(':', 1)
            key_part = key_part.strip()
            duration_str = duration_str.strip()
            
            # Check if it's a key combination
            if '+' in key_part:
                keys = key_part.split('+')
                for key in keys:
                    key = key.strip()
                    if key not in available_keys:
                        messagebox.showerror("Invalid Sequence", 
                                           f"Unknown key in combination: '{key}'. Available: {', '.join(available_keys[:20])}...")
                        return False
            else:
                # Single key
                if key_part not in available_keys:
                    messagebox.showerror("Invalid Sequence", 
                                       f"Unknown key: '{key_part}'. Available: {', '.join(available_keys[:20])}...")
                    return False
            
            # Validate duration
            try:
                duration = float(duration_str)
                if duration <= 0 or duration > 10:
                    messagebox.showerror("Invalid Sequence", 
                                       f"Duration must be between 0 and 10 seconds: '{duration_str}'")
                    return False
            except ValueError:
                messagebox.showerror("Invalid Sequence", 
                                   f"Invalid duration: '{duration_str}'. Must be a number.")
                return False
        
        return True
    
    def _validate_mouse_sequence(self, steps: list) -> bool:
        """Validate mouse sequence format."""
        valid_actions = ["click", "doubleclick", "move", "scroll"]
        
        for step in steps:
            step = step.strip()
            if ':' not in step:
                messagebox.showerror("Invalid Sequence", 
                                   f"Invalid step format: '{step}'. Use ACTION:params:duration format.")
                return False
            
            parts = step.split(':')
            if len(parts) < 2:
                messagebox.showerror("Invalid Sequence", 
                                   f"Invalid mouse action format: '{step}'")
                return False
            
            action = parts[0].strip()
            
            # Check if action is valid
            if action not in valid_actions and not any(action.startswith(va) for va in valid_actions):
                messagebox.showerror("Invalid Sequence", 
                                   f"Unknown mouse action: '{action}'. Available: {', '.join(valid_actions)}")
                return False
            
            # Validate duration (last part)
            try:
                duration = float(parts[-1])
                if duration <= 0 or duration > 10:
                    messagebox.showerror("Invalid Sequence", 
                                       f"Duration must be between 0 and 10 seconds: '{parts[-1]}'")
                    return False
            except ValueError:
                messagebox.showerror("Invalid Sequence", 
                                   f"Invalid duration: '{parts[-1]}'. Must be a number.")
                return False
        
        return True
    
    def _capture_template(self):
        """Capture a template image from screen."""
        try:
            # Get capture area size from settings
            try:
                width = int(self.capture_width_entry.get() or "100")
                height = int(self.capture_height_entry.get() or "100")
            except ValueError:
                width, height = 100, 100
                self._add_log("Using default capture size 100x100")
            
            # Get template name
            template_name = self.template_name_entry.get().strip()
            if not template_name:
                self.show_centered_messagebox("No Template Name", "Please enter a template name first", "error")
                return
            
            # Remove .png extension if present
            if template_name.endswith('.png'):
                template_name = template_name[:-4]
            
            self._add_log(f"Starting template capture for '{template_name}'")
            self._add_log("Click on the area you want to capture...")
            
            # Start capture in separate thread
            threading.Thread(target=self._capture_template_worker, 
                           args=(template_name, width, height), daemon=True).start()
            
        except Exception as e:
            self._add_log(f"Error starting template capture: {e}")
    
    def _capture_template_worker(self, template_name: str, width: int, height: int):
        """Worker thread for template capture."""
        try:
            import time
            import tkinter as tk
            
            # Hide main window temporarily
            self.root.withdraw()
            
            # Wait a moment for window to hide
            time.sleep(0.5)
            
            # Create overlay window to capture click
            capture_window = tk.Toplevel()
            capture_window.attributes('-fullscreen', True)
            capture_window.attributes('-alpha', 0.3)
            capture_window.configure(bg='red')
            capture_window.attributes('-topmost', True)
            
            # Add instruction label
            instruction = tk.Label(capture_window, 
                                 text=f"Click to capture template '{template_name}'\nPress ESC to cancel",
                                 font=("Arial", 24), bg='red', fg='white')
            instruction.pack(expand=True)
            
            captured = False
            capture_pos = None
            
            def on_click(event):
                nonlocal captured, capture_pos
                captured = True
                capture_pos = (event.x_root, event.y_root)
                capture_window.destroy()
            
            def on_escape(event):
                nonlocal captured
                captured = False
                capture_window.destroy()
            
            capture_window.bind('<Button-1>', on_click)
            capture_window.bind('<Escape>', on_escape)
            capture_window.focus_set()
            
            # Wait for capture window to close
            capture_window.wait_window()
            
            # Restore main window
            self.root.deiconify()
            
            if captured and capture_pos:
                # Capture the area
                screenshot = self.image_detector.capture_area_around_cursor(capture_pos, (width, height))
                
                if screenshot is not None:
                    # Save template
                    if self.image_detector.save_template(screenshot, template_name):
                        self._add_log(f"Template '{template_name}' captured and saved")
                        
                        # Update template name in GUI (add .png if not present)
                        if not self.template_name_entry.get().endswith('.png'):
                            self.template_name_entry.delete(0, "end")
                            self.template_name_entry.insert(0, f"{template_name}.png")
                    else:
                        self._add_log(f"Failed to save template '{template_name}'")
                else:
                    self._add_log("Failed to capture screenshot")
            else:
                self._add_log("Template capture cancelled")
                
        except Exception as e:
            # Ensure main window is restored
            try:
                self.root.deiconify()
            except:
                pass
            self._add_log(f"Error during template capture: {e}")
    
    def _import_templates(self):
        """Import multiple template files at once."""
        try:
            from tkinter import filedialog
            
            # Ask user to select multiple image files
            filetypes = [
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
            
            file_paths = self.show_centered_filedialog(
                "open_multiple",
                title="Select Template Images to Import",
                filetypes=filetypes
            )
            
            if not file_paths:
                return
            
            # Ensure templates directory exists
            templates_dir = "templates"
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            
            imported_count = 0
            skipped_count = 0
            error_count = 0
            
            self._add_log(f"Starting bulk template import: {len(file_paths)} files selected")
            
            for file_path in file_paths:
                try:
                    # Get filename without path
                    filename = os.path.basename(file_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    
                    # Convert to PNG if needed and copy to templates folder
                    target_path = os.path.join(templates_dir, f"{name_without_ext}.png")
                    
                    # Check if target already exists
                    if os.path.exists(target_path):
                        response = messagebox.askyesnocancel(
                            "Template Exists", 
                            f"Template '{name_without_ext}.png' already exists. Overwrite?\\n\\nYes = Overwrite\\nNo = Skip\\nCancel = Stop import"
                        )
                        if response is None:  # Cancel
                            break
                        elif response == False:  # No (skip)
                            self._add_log(f"Skipped: {filename} (already exists)")
                            skipped_count += 1
                            continue
                    
                    # Load and convert image
                    from PIL import Image
                    img = Image.open(file_path)
                    
                    # Convert to RGBA if needed (for PNG)
                    if img.mode not in ('RGBA', 'RGB'):
                        img = img.convert('RGBA')
                    
                    # Save as PNG in templates folder
                    img.save(target_path, 'PNG')
                    
                    self._add_log(f"Imported: {filename} -> {name_without_ext}.png")
                    imported_count += 1
                    
                except Exception as e:
                    self._add_log(f"Error importing {filename}: {e}")
                    error_count += 1
            
            # Summary
            summary = f"\\n=== IMPORT SUMMARY ===\\n"
            summary += f"Successfully imported: {imported_count} templates\\n"
            if skipped_count > 0:
                summary += f"Skipped (already exist): {skipped_count} templates\\n"
            if error_count > 0:
                summary += f"Errors encountered: {error_count} templates\\n"
            summary += f"Total templates now available: {len([f for f in os.listdir(templates_dir) if f.endswith('.png')] if os.path.exists(templates_dir) else [])}\\n"
            summary += f"\u2705 No limit on template count - import as many as you need!"
            
            self._add_log(summary)
            
            if imported_count > 0:
                messagebox.showinfo("Import Complete", 
                                  f"Successfully imported {imported_count} template(s).\\n\\n"
                                  f"You can now create detection rules using these templates.")
            
        except Exception as e:
            self._add_log(f"Error during bulk template import: {e}")
            messagebox.showerror("Import Error", f"Failed to import templates: {e}")
    
    # Configuration management methods
    def _save_config(self):
        """Save current configuration to file."""
        try:
            # Update config from GUI first
            self._save_gui_to_config()
            
            # Ask for filename with centered dialog
            temp_window = tk.Toplevel(self.root)
            temp_window.withdraw()  # Hide the temporary window
            self.center_dialog_on_main(temp_window)
            
            filename = tk.simpledialog.askstring("Save Configuration", 
                                                "Enter configuration name:", 
                                                initialvalue="my_config.json",
                                                parent=temp_window)
            
            temp_window.destroy()  # Clean up
            
            if filename:
                # Ensure .json extension
                if not filename.endswith('.json'):
                    filename += '.json'
                
                if self.config_manager.save_config(filename):
                    self._add_log(f"Configuration saved as '{filename}'")
                    self.show_centered_messagebox("Success", f"Configuration saved as '{filename}'", "info")
                else:
                    self._add_log(f"Failed to save configuration '{filename}'")
                    messagebox.showerror("Error", f"Failed to save configuration '{filename}'")
            
        except Exception as e:
            self._add_log(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            # Get available config files
            config_files = self.config_manager.get_config_files()
            
            if not config_files:
                self.show_centered_messagebox("No Configurations", "No configuration files found", "info")
                return
            
            # Let user choose config file
            choice_window = tk.Toplevel(self.root)
            choice_window.title("Load Configuration")
            choice_window.geometry("400x300")
            choice_window.transient(self.root)
            choice_window.grab_set()
            
            tk.Label(choice_window, text="Select configuration to load:", 
                    font=("Arial", 12)).pack(pady=10)
            
            # Listbox for config files
            listbox = tk.Listbox(choice_window, height=10)
            listbox.pack(fill="both", expand=True, padx=20, pady=10)
            
            for config_file in config_files:
                listbox.insert("end", config_file)
            
            selected_file = None
            
            def on_load():
                nonlocal selected_file
                selection = listbox.curselection()
                if selection:
                    selected_file = config_files[selection[0]]
                    choice_window.destroy()
            
            def on_cancel():
                choice_window.destroy()
            
            # Buttons
            btn_frame = tk.Frame(choice_window)
            btn_frame.pack(pady=10)
            
            tk.Button(btn_frame, text="Load", command=on_load, width=10).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side="left", padx=5)
            
            # Wait for window to close
            choice_window.wait_window()
            
            if selected_file:
                if self.config_manager.load_config(selected_file):
                    self._add_log(f"Configuration loaded from '{selected_file}'")
                    
                    # Clear GUI and reload
                    self._clear_gui_fields()
                    self._load_config_to_gui()
                    
                    self.show_centered_messagebox("Success", f"Configuration loaded from '{selected_file}'", "info")
                else:
                    self._add_log(f"Failed to load configuration '{selected_file}'")
                    messagebox.showerror("Error", f"Failed to load configuration '{selected_file}'")
            
        except Exception as e:
            self._add_log(f"Error loading configuration: {e}")
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def _export_config(self):
        """Export configuration to chosen location."""
        try:
            # Update config from GUI first
            self._save_gui_to_config()
            
            # Ask for export location
            filename = self.show_centered_filedialog(
                "save",
                title="Export Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                if self.config_manager.export_config(filename):
                    self._add_log(f"Configuration exported to '{filename}'")
                    messagebox.showinfo("Success", f"Configuration exported to '{filename}'")
                else:
                    self._add_log(f"Failed to export configuration to '{filename}'")
                    messagebox.showerror("Error", f"Failed to export configuration")
            
        except Exception as e:
            self._add_log(f"Error exporting configuration: {e}")
            messagebox.showerror("Error", f"Failed to export configuration: {e}")
    
    def _import_config(self):
        """Import configuration from chosen file."""
        try:
            # Ask for import file
            filename = self.show_centered_filedialog(
                "open",
                title="Import Configuration",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                if self.config_manager.import_config(filename):
                    self._add_log(f"Configuration imported from '{filename}'")
                    
                    # Clear GUI and reload
                    self._clear_gui_fields()
                    self._load_config_to_gui()
                    
                    messagebox.showinfo("Success", f"Configuration imported from '{filename}'")
                else:
                    self._add_log(f"Failed to import configuration from '{filename}'")
                    messagebox.showerror("Error", f"Failed to import configuration")
            
        except Exception as e:
            self._add_log(f"Error importing configuration: {e}")
            messagebox.showerror("Error", f"Failed to import configuration: {e}")
    
    def _show_template_stats(self):
        """Show comprehensive template statistics and management info."""
        try:
            stats = self.config_manager.get_template_statistics()
            
            stats_text = f"=== TEMPLATE STATISTICS ===\\n\\n"
            stats_text += f"📊 Total Templates: {stats['total_templates']}\\n"
            stats_text += f"💾 Total Size: {stats['total_size_bytes']:,} bytes ({stats['total_size_bytes']/(1024*1024):.1f} MB)\\n"
            
            if stats['total_templates'] > 0:
                stats_text += f"📏 Average Size: {stats['average_size_bytes']:,} bytes\\n"
                
                if stats['largest_template']:
                    largest = stats['largest_template']
                    stats_text += f"📈 Largest: {largest['name']} ({largest['size']:,} bytes)\\n"
                
                if stats['smallest_template']:
                    smallest = stats['smallest_template']
                    stats_text += f"📉 Smallest: {smallest['name']} ({smallest['size']:,} bytes)\\n"
            
            stats_text += f"\\n🚀 UNLIMITED SUPPORT: ✅\\n"
            stats_text += f"• No limit on number of templates\\n"
            stats_text += f"• No limit on template file sizes\\n"
            stats_text += f"• Performance optimized for large datasets\\n"
            
            # Template usage analysis
            if stats['template_usage_count']:
                most_used = max(stats['template_usage_count'].items(), key=lambda x: x[1])
                stats_text += f"\\n📈 Most Used Template: {most_used[0]} ({most_used[1]} rules)\\n"
            
            # Unused templates
            if stats['templates_without_rules']:
                count = len(stats['templates_without_rules'])
                stats_text += f"\\n⚠️ Unused Templates: {count}\\n"
                if count <= 10:
                    for template in stats['templates_without_rules']:
                        stats_text += f"  • {template}\\n"
                else:
                    for template in stats['templates_without_rules'][:5]:
                        stats_text += f"  • {template}\\n"
                    stats_text += f"  ... and {count-5} more\\n"
            
            # Missing templates
            if stats['rules_without_templates']:
                count = len(stats['rules_without_templates'])
                stats_text += f"\\n❌ Missing Templates: {count}\\n"
                for missing in stats['rules_without_templates'][:10]:
                    stats_text += f"  • Rule '{missing['rule_name']}' needs '{missing['template_name']}'\\n"
                if count > 10:
                    stats_text += f"  ... and {count-10} more\\n"
            
            if stats['total_templates'] >= 100:
                stats_text += f"\\n🎯 PERFORMANCE TIPS:\\n"
                stats_text += f"• Large template collections work great!\\n"
                stats_text += f"• Consider organizing by game/application\\n"
                stats_text += f"• Use descriptive template names\\n"
                stats_text += f"• Remove unused templates to save disk space\\n"
            
            if 'error' in stats:
                stats_text += f"\\n❌ Error: {stats['error']}\\n"
            
            self._add_log(stats_text)
            
            # Also show in popup for better visibility
            popup = tk.Toplevel(self.root)
            popup.title("Template Statistics")
            popup.geometry("600x500")
            popup.configure(bg="#2b2b2b")
            
            text_widget = tk.Text(popup, bg="#2b2b2b", fg="white", font=("Consolas", 10))
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", stats_text)
            text_widget.config(state="disabled")
            
            close_btn = tk.Button(popup, text="Close", command=popup.destroy)
            close_btn.pack(pady=5)
            
        except Exception as e:
            self._add_log(f"Error generating template statistics: {e}")
            messagebox.showerror("Error", f"Failed to generate template statistics: {e}")
    
    def _clear_gui_fields(self):
        """Clear all GUI input fields."""
        try:
            # Window config
            self.window_title_entry.delete(0, "end")
            self.window_width_entry.delete(0, "end")
            self.window_height_entry.delete(0, "end")
            
            # Bot config
            self.loop_delay_entry.delete(0, "end")
            self.action_cooldown_entry.delete(0, "end")
            self.capture_width_entry.delete(0, "end")
            self.capture_height_entry.delete(0, "end")
            
            # Joystick config
            self.joystick_delay_entry.delete(0, "end")
            
            # Rule details
            self.rule_name_entry.delete(0, "end")
            self.template_name_entry.delete(0, "end")
            self.confidence_slider.set(0.8)
            self.action_combobox.set("A")
            
            # Clear rules list
            self.rules_listbox.delete(0, "end")
            self.selected_rule_index = None
            
        except Exception as e:
            self._add_log(f"Error clearing GUI fields: {e}")
    
    def _browse_templates(self):
        """Show available templates for selection with adaptive sizing."""
        try:
            # Get available templates
            available_templates = []
            templates_dir = "templates"
            
            if os.path.exists(templates_dir):
                for file in os.listdir(templates_dir):
                    if file.endswith('.png'):
                        available_templates.append(file)
            
            if not available_templates:
                self.show_centered_messagebox("No Templates", "No template files found in templates/ directory", "info")
                return
            
            # Calculate optimal window size based on content
            dialog_size = self._calculate_template_dialog_size(available_templates)
            dialog_geometry = self._load_template_dialog_geometry(dialog_size)
            
            # Create selection window
            selection_window = tk.Toplevel(self.root)
            selection_window.title("Select Template")
            selection_window.geometry(dialog_geometry)
            selection_window.transient(self.root)
            selection_window.grab_set()
            
            # Make window resizable
            selection_window.resizable(True, True)
            selection_window.minsize(350, 250)
            selection_window.maxsize(800, 600)
            
            # Center the selection window
            self.center_dialog_on_main(selection_window)
            
            # Header frame
            header_frame = tk.Frame(selection_window)
            header_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            tk.Label(header_frame, text="Available Templates:", font=("Arial", 12, "bold")).pack(side="left")
            
            # Template count label
            count_label = tk.Label(header_frame, text=f"({len(available_templates)} templates)", 
                                 font=("Arial", 10), fg="gray")
            count_label.pack(side="right")
            
            # Listbox frame with scrollbars
            listbox_frame = tk.Frame(selection_window)
            listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Create listbox with scrollbars
            listbox = tk.Listbox(listbox_frame, font=("Consolas", 10))
            v_scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
            h_scrollbar = tk.Scrollbar(listbox_frame, orient="horizontal", command=listbox.xview)
            
            listbox.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Grid layout for listbox and scrollbars
            listbox.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            listbox_frame.grid_rowconfigure(0, weight=1)
            listbox_frame.grid_columnconfigure(0, weight=1)
            
            # Add templates to listbox (sorted for better user experience)
            sorted_templates = sorted(available_templates, key=str.lower)
            for template in sorted_templates:
                listbox.insert("end", template)
            
            # Status frame
            status_frame = tk.Frame(selection_window)
            status_frame.pack(fill="x", padx=10, pady=5)
            
            status_label = tk.Label(status_frame, text="Double-click to select, or use buttons below", 
                                  font=("Arial", 9), fg="gray")
            status_label.pack()
            
            selected_template = None
            
            def on_select():
                nonlocal selected_template
                selection = listbox.curselection()
                if selection:
                    selected_template = sorted_templates[selection[0]]
                    self._save_template_dialog_geometry(selection_window)
                    selection_window.destroy()
            
            def on_double_click(event):
                on_select()
            
            def on_preview():
                selection = listbox.curselection()
                if selection:
                    template_name = sorted_templates[selection[0]]
                    self._show_template_preview(template_name)
            
            def on_cancel():
                self._save_template_dialog_geometry(selection_window)
                selection_window.destroy()
            
            # Bind double-click
            listbox.bind('<Double-Button-1>', on_double_click)
            
            # Buttons frame
            btn_frame = tk.Frame(selection_window)
            btn_frame.pack(fill="x", padx=10, pady=(5, 10))
            
            # Button styling
            btn_style = {"width": 12, "height": 1}
            
            tk.Button(btn_frame, text="✓ Select", command=on_select, bg="#4CAF50", fg="white", **btn_style).pack(side="left", padx=5)
            tk.Button(btn_frame, text="👁 Preview", command=on_preview, bg="#2196F3", fg="white", **btn_style).pack(side="left", padx=5)
            tk.Button(btn_frame, text="✕ Cancel", command=on_cancel, **btn_style).pack(side="right", padx=5)
            
            # Bind window close event to save geometry
            selection_window.protocol("WM_DELETE_WINDOW", on_cancel)
            
            # Auto-select first item for convenience
            if sorted_templates:
                listbox.selection_set(0)
                listbox.focus_set()
            
            # Wait for window to close
            selection_window.wait_window()
            
            if selected_template:
                self.template_name_entry.delete(0, "end")
                self.template_name_entry.insert(0, selected_template)
                self._add_log(f"Template selected: {selected_template}")
                
        except Exception as e:
            self._add_log(f"Error browsing templates: {e}")
    
    def _preview_template(self):
        """Preview the currently selected template."""
        try:
            template_name = self.template_name_entry.get().strip()
            if not template_name:
                messagebox.showwarning("No Template", "Please enter or select a template name first")
                return
            
            # Remove .png if present and add it back
            if template_name.endswith('.png'):
                template_name = template_name[:-4]
            
            self._show_template_preview(template_name + '.png')
            
        except Exception as e:
            self._add_log(f"Error previewing template: {e}")
    
    def _show_template_preview(self, template_filename: str):
        """Show template preview window with enhanced sizing and persistence."""
        try:
            import cv2
            from PIL import Image, ImageTk
            
            template_path = os.path.join("templates", template_filename)
            
            if not os.path.exists(template_path):
                self.show_centered_messagebox("Template Not Found", f"Template file not found: {template_path}", "error")
                return
            
            # Load template image
            template_cv = cv2.imread(template_path)
            if template_cv is None:
                self.show_centered_messagebox("Error", f"Could not load template: {template_path}", "error")
                return
            
            # Convert BGR to RGB for display
            template_rgb = cv2.cvtColor(template_cv, cv2.COLOR_BGR2RGB)
            
            # Calculate optimal preview window size based on image dimensions
            image_height, image_width = template_cv.shape[:2]
            dialog_size = self._calculate_preview_dialog_size(image_width, image_height)
            dialog_geometry = self._load_preview_dialog_geometry(dialog_size)
            
            # Create preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"Template Preview: {template_filename}")
            preview_window.geometry(dialog_geometry)
            preview_window.transient(self.root)
            preview_window.resizable(True, True)
            preview_window.minsize(300, 200)
            
            # Center the preview window
            self.center_dialog_on_main(preview_window)
            
            # Header frame
            header_frame = tk.Frame(preview_window)
            header_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            # Template info
            filename_label = tk.Label(header_frame, text=f"📁 {template_filename}", 
                                    font=("Arial", 12, "bold"))
            filename_label.pack(side="left")
            
            # Image dimensions info
            size_label = tk.Label(header_frame, text=f"{image_width}×{image_height} px", 
                                font=("Arial", 10), fg="gray")
            size_label.pack(side="right")
            
            # Image frame with scrollable canvas
            image_frame = tk.Frame(preview_window)
            image_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Create canvas with scrollbars for large images
            canvas = tk.Canvas(image_frame, bg="white")
            v_scrollbar = tk.Scrollbar(image_frame, orient="vertical", command=canvas.yview)
            h_scrollbar = tk.Scrollbar(image_frame, orient="horizontal", command=canvas.xview)
            
            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Create scrollable frame
            scrollable_frame = tk.Frame(canvas)
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            
            # Convert to PhotoImage for display
            pil_image = Image.fromarray(template_rgb)
            
            # Scale image if it's too large for comfortable viewing
            max_display_size = (600, 400)
            display_image = pil_image.copy()
            display_image.thumbnail(max_display_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(display_image)
            
            # Display image
            image_label = tk.Label(scrollable_frame, image=photo, bg="white")
            image_label.image = photo  # Keep a reference
            image_label.pack(padx=10, pady=10)
            
            # Grid layout for canvas and scrollbars
            canvas.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            image_frame.grid_rowconfigure(0, weight=1)
            image_frame.grid_columnconfigure(0, weight=1)
            
            # Info frame
            info_frame = tk.Frame(preview_window)
            info_frame.pack(fill="x", padx=10, pady=5)
            
            # File info
            file_size = os.path.getsize(template_path)
            file_size_str = f"{file_size} bytes"
            if file_size > 1024:
                file_size_str = f"{file_size/1024:.1f} KB"
            
            info_text = f"File Size: {file_size_str} | Original: {image_width}×{image_height}"
            if display_image.size != pil_image.size:
                info_text += f" | Displayed: {display_image.size[0]}×{display_image.size[1]}"
                
            info_label = tk.Label(info_frame, text=info_text, font=("Arial", 9), fg="gray")
            info_label.pack()
            
            # Buttons frame
            btn_frame = tk.Frame(preview_window)
            btn_frame.pack(fill="x", padx=10, pady=(5, 10))
            
            # Test detection button
            def test_detection():
                self._save_preview_dialog_geometry(preview_window)
                preview_window.destroy()
                self._test_template_detection(template_filename)
            
            def close_preview():
                self._save_preview_dialog_geometry(preview_window)
                preview_window.destroy()
            
            # Button styling
            btn_style = {"height": 1, "width": 15}
            
            test_btn = tk.Button(btn_frame, text="🔍 Test Detection", command=test_detection, 
                               bg="#FF9800", fg="white", **btn_style)
            test_btn.pack(side="left", padx=5)
            
            close_btn = tk.Button(btn_frame, text="✕ Close", command=close_preview, **btn_style)
            close_btn.pack(side="right", padx=5)
            
            # Bind window close event
            preview_window.protocol("WM_DELETE_WINDOW", close_preview)
            
            # Bind mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            canvas.bind("<MouseWheel>", _on_mousewheel)
            
        except Exception as e:
            self.show_centered_messagebox("Preview Error", f"Error showing preview: {e}", "error")
    
    def _test_template_detection(self, template_filename: str):
        """Test template detection and show results."""
        try:
            self._add_log(f"Testing detection for: {template_filename}")
            
            # Run template detection test in background
            def run_test():
                try:
                    # Find window
                    windows = self.window_manager.find_windows_by_title(self.window_title_entry.get() or "Xbox")
                    if not windows:
                        self._add_log("❌ No target window found for testing")
                        return
                    
                    window = windows[0]
                    capture_area = self.window_manager.capture_window_area(window)
                    if not capture_area:
                        self._add_log("❌ Could not get window capture area")
                        return
                    
                    screenshot = self.image_detector.capture_screenshot(capture_area)
                    if screenshot is None:
                        self._add_log("❌ Could not capture screenshot")
                        return
                    
                    # Test different confidence levels
                    template_name = template_filename[:-4] if template_filename.endswith('.png') else template_filename
                    confidence_levels = [0.5, 0.6, 0.7, 0.8, 0.9]
                    
                    self._add_log(f"📊 Detection test results for {template_filename}:")
                    
                    found_any = False
                    best_confidence = 0.0
                    
                    for confidence in confidence_levels:
                        match = self.image_detector.find_template(screenshot, template_name, confidence)
                        if match:
                            self._add_log(f"   ✅ Confidence {confidence:.1f}: FOUND (actual: {match['confidence']:.3f})")
                            found_any = True
                            best_confidence = max(best_confidence, match['confidence'])
                        else:
                            self._add_log(f"   ❌ Confidence {confidence:.1f}: not found")
                    
                    if found_any:
                        recommended_confidence = max(0.5, best_confidence - 0.1)
                        self._add_log(f"💡 Recommendation: Set confidence to {recommended_confidence:.1f} or lower")
                    else:
                        self._add_log(f"⚠️ Template not detected at any confidence level")
                        self._add_log(f"   Consider recapturing the template or checking if image is on screen")
                    
                except Exception as e:
                    self._add_log(f"Error during detection test: {e}")
            
            # Run in background thread
            import threading
            threading.Thread(target=run_test, daemon=True).start()
            
        except Exception as e:
            self._add_log(f"Error starting detection test: {e}")
    
    def _on_action_type_change(self):
        """Handle action type change between simple and sequence."""
        try:
            action_type = self.action_type_var.get()
            
            if action_type == "simple":
                self.simple_action_frame.pack(fill="x", padx=5, pady=2)
                self.sequence_action_frame.pack_forget()
            else:  # sequence
                self.simple_action_frame.pack_forget()
                self.sequence_action_frame.pack(fill="x", padx=5, pady=2)
                
        except Exception as e:
            self._add_log(f"Error changing action type: {e}")
    
    def _on_input_mode_change(self, selected_mode=None):
        """Handle input mode change to update available actions."""
        try:
            input_mode = self.input_mode_combobox.get()
            
            # Import new enums
            from modules.virtual_controller import KeyboardKey, MouseButton, XboxButton
            
            if input_mode == "controller":
                # Update to controller buttons
                available_actions = [button.value for button in XboxButton]
                self.action_combobox.configure(values=available_actions)
                self.action_combobox.set("A")
                self.simple_action_label.configure(text="Button:")
                
                # Update sequence placeholder
                self.sequence_entry.configure(
                    placeholder_text="A:0.1,STICK_UP:2.0,B:0.2"
                )
                
            elif input_mode == "keyboard":
                # Update to keyboard keys
                available_actions = [key.value for key in KeyboardKey]
                # Add common combinations
                available_actions.extend(["ctrl+c", "ctrl+v", "alt+tab", "ctrl+z"])
                self.action_combobox.configure(values=available_actions)
                self.action_combobox.set("space")
                self.simple_action_label.configure(text="Key:")
                
                # Update sequence placeholder
                self.sequence_entry.configure(
                    placeholder_text="w:2.0,ctrl+c:0.1,v:0.1"
                )
                
            elif input_mode == "mouse":
                # Update to mouse actions
                available_actions = [
                    "click", "click:left", "click:right", "click:middle",
                    "doubleclick", "doubleclick:left",
                    "move:100:200", "scroll:up", "scroll:down"
                ]
                self.action_combobox.configure(values=available_actions)
                self.action_combobox.set("click")
                self.simple_action_label.configure(text="Action:")
                
                # Update sequence placeholder
                self.sequence_entry.configure(
                    placeholder_text="click:0.1,move:100:200:0.5,click:0.1"
                )
                
        except Exception as e:
            self._add_log(f"Error changing input mode: {e}")
    
    def _show_sequence_help(self):
        """Show help for sequence format."""
        help_text = """
=== SEQUENCE FORMAT HELP ===

🎮 CONTROLLER MODE:
Format: BUTTON1:duration,BUTTON2:duration,BUTTON3:duration

Available Buttons:
- A, B, X, Y (face buttons)
- DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT (directional pad)  
- STICK_UP, STICK_DOWN, STICK_LEFT, STICK_RIGHT (left joystick movement)
- STICK_UP_LEFT, STICK_UP_RIGHT, STICK_DOWN_LEFT, STICK_DOWN_RIGHT (diagonal)
- STICK_CENTER (return stick to center)
- LB, RB (shoulder buttons)
- START, BACK (system buttons)
- LEFT_THUMB, RIGHT_THUMB (stick clicks)

Examples:
🎮 Joystick movement: STICK_UP:2.0,STICK_LEFT:1.5,STICK_RIGHT:1.0
🎮 Jump and move: A:0.2,STICK_UP:1.0
🎮 Circle movement: STICK_UP:1,STICK_RIGHT:1,STICK_DOWN:1,STICK_LEFT:1
🎮 Complex combo: X:0.1,Y:0.1,STICK_DOWN:0.5,A:0.2

⌨️ KEYBOARD MODE:
Format: KEY1:duration,KEY2:duration,COMBO1+COMBO2:duration

Available Keys:
- Letters: a-z
- Numbers: 0-9
- Special: space, enter, tab, esc, backspace, delete
- Arrows: up, down, left, right
- Function: f1-f12
- Modifiers: ctrl, alt, shift, win

Examples:
⌨️ Movement: w:2.0,a:1.0,d:1.0
⌨️ Copy/Paste: ctrl+a:0.1,ctrl+c:0.1,ctrl+v:0.1
⌨️ Alt-Tab: alt+tab:0.1
⌨️ Text entry: h:0.1,e:0.1,l:0.1,l:0.1,o:0.1

🖱️ MOUSE MODE:
Format: ACTION:params:duration,ACTION:params:duration

Available Actions:
- click, click:left, click:right, click:middle
- doubleclick, doubleclick:left
- move:x:y (move to coordinates)
- scroll:up, scroll:down, scroll:up:5 (amount)

Examples:
🖱️ Click sequence: click:0.1,move:100:200:0.5,click:0.1
🖱️ Right-click menu: click:right:0.1,move:150:250:0.2,click:left:0.1
🖱️ Scroll and click: scroll:down:3:0.5,click:0.1

Notes:
- Duration is in seconds (0.1 = 100ms)
- Use shorter durations (0.1-0.5s) for quick actions
- Use longer durations (1-3s) for movement
- Key combinations use + (ctrl+c, alt+tab)
- Mouse coordinates are absolute screen positions
"""
        self._add_log(help_text)
    
    def _on_closing(self):
        """Handle application closing."""
        # Cancel any pending geometry save timer
        if self.geometry_save_timer:
            self.root.after_cancel(self.geometry_save_timer)
            self.geometry_save_timer = None
        
        # Save window geometry before closing (final save)
        self._save_window_geometry()
        
        # Stop KB2JOY if running
        if hasattr(self, 'kb2joy_enabled') and self.kb2joy_enabled:
            self._stop_kb2joy()
        
        if self.bot_thread and self.bot_thread.is_running():
            if self.show_centered_messagebox("Confirm Exit", "Bot is running. Stop bot and exit?", "question"):
                self.bot_thread.stop_bot()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def _toggle_rule_enabled(self, rule_index: int):
        """Toggle the enabled state of a rule."""
        try:
            if 0 <= rule_index < len(self.current_rules):
                rule = self.current_rules[rule_index]
                
                # Toggle the enabled state in config
                success = self.config_manager.toggle_rule_enabled(rule.name)
                
                if success:
                    # Update the rule object
                    rule.enabled = not rule.enabled
                    
                    # Refresh the table to show updated state
                    self._refresh_rules_list()
                    
                    state_text = "enabled" if rule.enabled else "disabled"
                    self._add_log(f"Rule '{rule.name}' {state_text}")
                else:
                    self._add_log(f"Failed to toggle rule '{rule.name}'")
        except Exception as e:
            self._add_log(f"Error toggling rule: {e}")
    
    def _show_template_preview_popup(self, rule_index: int):
        """Show template preview in a popup window."""
        try:
            if 0 <= rule_index < len(self.current_rules):
                rule = self.current_rules[rule_index]
                template_path = os.path.join("templates", rule.template)
                
                if not template_path.endswith('.png'):
                    template_path += '.png'
                
                if os.path.exists(template_path):
                    # Create popup window
                    popup = tk.Toplevel(self.root)
                    popup.title(f"Template Preview - {rule.template}")
                    popup.geometry("400x400")
                    popup.configure(bg="#2b2b2b")
                    
                    # Center the popup window
                    self.center_dialog_on_main(popup)
                    
                    # Load and display image
                    img = Image.open(template_path)
                    
                    # Scale image to fit popup while maintaining aspect ratio
                    max_size = 350
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Use regular PhotoImage for tk.Label in popup (not CTkLabel)
                    photo = ImageTk.PhotoImage(img)
                    
                    label = tk.Label(popup, image=photo, bg="#2b2b2b")
                    label.pack(pady=20)
                    
                    # Info label
                    info_text = f"Template: {rule.template}\\nRule: {rule.name}\\nAction: {rule.action}"
                    info_label = tk.Label(popup, text=info_text, bg="#2b2b2b", fg="white", font=("Arial", 10))
                    info_label.pack(pady=10)
                    
                    # Keep reference to prevent garbage collection
                    label.image = photo
                    
                    # Center popup
                    popup.transient(self.root)
                    popup.grab_set()
                else:
                    messagebox.showerror("Template Not Found", f"Template file '{rule.template}' not found in templates folder.")
        except Exception as e:
            self._add_log(f"Error showing template preview: {e}")
            messagebox.showerror("Preview Error", f"Failed to show template preview: {e}")
    
    # KB2JOY Methods
    
    def _install_pynput(self):
        """Install pynput library."""
        try:
            import subprocess
            import sys
            
            self._add_log("Installing pynput library...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "pynput"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self._add_log("pynput installed successfully! Please restart the application.")
                self.show_centered_messagebox("Success", "pynput installed successfully! Please restart the application.", "info")
            else:
                self._add_log(f"Failed to install pynput: {result.stderr}")
                self.show_centered_messagebox("Error", f"Failed to install pynput: {result.stderr}", "error")
                
        except Exception as e:
            self._add_log(f"Error installing pynput: {e}")
            self.show_centered_messagebox("Error", f"Error installing pynput: {e}", "error")
    
    def _toggle_kb2joy(self):
        """Toggle KB2JOY on/off."""
        if not PYNPUT_AVAILABLE:
            self.show_centered_messagebox("Error", "pynput library is required for KB2JOY functionality", "error")
            self.kb2joy_enabled_var.set(False)
            return
        
        if self.kb2joy_enabled_var.get():
            self._start_kb2joy()
        else:
            self._stop_kb2joy()
    
    def _start_kb2joy(self):
        """Start KB2JOY input capture."""
        try:
            if not PYNPUT_AVAILABLE:
                return
            
            # Stop any existing listeners
            self._stop_kb2joy()
            
            # Check if suppress setting is enabled
            suppress_enabled = self.kb2joy_suppress_input_var.get() if hasattr(self, 'kb2joy_suppress_input_var') else True
            
            # Use a more robust approach - start without suppression and use a monitoring system
            if suppress_enabled:
                self._add_log("🔒 Attempting advanced suppression mode with monitoring")
                # Try suppression with careful monitoring
                try:
                    self.kb2joy_listener = keyboard.Listener(
                        on_press=self._on_kb2joy_key_press_monitored,
                        on_release=self._on_kb2joy_key_release,
                        suppress=True  # Enable suppression with monitoring
                    )
                    self.kb2joy_suppression_active = True
                    self.kb2joy_last_activity = time.time()
                except Exception as e:
                    self._add_log(f"Suppression setup failed: {e}")
                    # Fall back to non-suppression
                    self.kb2joy_listener = keyboard.Listener(
                        on_press=self._on_kb2joy_key_press,
                        on_release=self._on_kb2joy_key_release,
                        suppress=False
                    )
                    self.kb2joy_suppression_active = False
            else:
                self._add_log("🔓 Using conversion-only mode")
                # Use without suppression
                self.kb2joy_listener = keyboard.Listener(
                    on_press=self._on_kb2joy_key_press,
                    on_release=self._on_kb2joy_key_release,
                    suppress=False
                )
                self.kb2joy_suppression_active = False
            
            # Create mouse listener without suppression (always safe)
            self.kb2joy_mouse_listener = mouse.Listener(
                on_click=self._on_kb2joy_mouse_click,
                on_scroll=self._on_kb2joy_mouse_scroll,
                suppress=False  # Mouse suppression disabled for safety
            )
            
            # Store the suppress setting
            self.kb2joy_suppress_enabled = suppress_enabled
            
            # Start listeners with error handling
            try:
                self.kb2joy_listener.start()
                self.kb2joy_mouse_listener.start()
                
                self.kb2joy_enabled = True
                self.kb2joy_status_label.configure(text="Status: Active - Capturing inputs")
                self._add_log("KB2JOY started - capturing keyboard and mouse inputs")
                
                # Use conversion-only mode for reliability
                if suppress_enabled and self.kb2joy_suppression_active:
                    self._add_log("🔄 KB2JOY running in CONVERSION mode")
                    self._add_log("💡 Original keyboard input will pass through - suppression disabled for reliability")
                    self._add_log("✅ Mapped keys will be converted to controller input")
                    self._start_suppression_monitoring()
                elif suppress_enabled:
                    self.root.after(2000, self._test_suppression_working)
                
            except Exception as e:
                self._add_log(f"Error starting KB2JOY listeners: {e}")
                # Try fallback mode
                self._start_kb2joy_fallback_mode()
            
            if suppress_enabled:
                self._add_log("🔒 Attempting keyboard suppression mode")
                self._add_log("⚠️  If keys still pass through, try running as Administrator")
                self._add_log("⚠️  Will automatically fall back to conversion-only if suppression fails")
            else:
                self._add_log("🔓 Conversion-only mode - original inputs will pass through")
            
            self._add_log(f"Target mode: {'SUPPRESSION' if suppress_enabled else 'CONVERSION-ONLY'}")
            
        except Exception as e:
            self._add_log(f"Error starting KB2JOY: {e}")
            self.show_centered_messagebox("Error", f"Failed to start KB2JOY: {e}", "error")
            self.kb2joy_enabled_var.set(False)
    
    def _stop_kb2joy(self):
        """Stop KB2JOY input capture."""
        try:
            self.kb2joy_enabled = False
            self.kb2joy_suppression_active = False
            
            # Stop pynput listeners
            if self.kb2joy_listener:
                self.kb2joy_listener.stop()
                self.kb2joy_listener = None
            
            if self.kb2joy_mouse_listener:
                self.kb2joy_mouse_listener.stop()
                self.kb2joy_mouse_listener = None
            
            # Uninstall Windows keyboard hook if it was installed
            if self.kb2joy_hook_installed:
                self._uninstall_keyboard_hook()
            
            # Clear suppressed keys
            self.kb2joy_suppressed_keys.clear()
            
            # Cancel monitoring timer
            if hasattr(self, 'kb2joy_monitor_timer') and self.kb2joy_monitor_timer:
                self.root.after_cancel(self.kb2joy_monitor_timer)
                self.kb2joy_monitor_timer = None
            
            self.kb2joy_status_label.configure(text="Status: Disabled")
            self._add_log("🔓 KB2JOY stopped - all suppression disabled")
            
        except Exception as e:
            self._add_log(f"Error stopping KB2JOY: {e}")
    
    def _on_kb2joy_key_press(self, key):
        """Handle keyboard key press events. Always returns True to keep listener active."""
        if not self.kb2joy_enabled or self.kb2joy_capture_mode:
            return  # Don't process, but keep listener active
        
        try:
            # Convert key to string representation
            key_str = self._key_to_string(key)
            
            # Check if this key is mapped to any Xbox button
            for xbox_button, mapped_input in self.kb2joy_mappings.items():
                if mapped_input == key_str:
                    # Send Xbox controller input
                    button = self.virtual_controller.get_button_from_string(xbox_button)
                    if button:
                        self.virtual_controller.press_button(button, duration=0.1)
                        
                        # Log the conversion
                        should_suppress = self.kb2joy_suppress_enabled
                        
                        if should_suppress:
                            self._add_log(f"KB2JOY: {key_str} -> {xbox_button} [CONVERTED - original may pass through]")
                        else:
                            self._add_log(f"KB2JOY: {key_str} -> {xbox_button} [CONVERTED - pass-through mode]")
                        
                        # Break after first match to avoid multiple conversions
                        break
                    
        except Exception as e:
            self._add_log(f"Error processing key press: {e}")
        
        # Always return True (or None) to keep the listener active
        # This prevents the "stops after first key" issue
    
    def _on_kb2joy_key_press_monitored(self, key):
        """Handle keyboard key press with suppression and activity monitoring."""
        if not self.kb2joy_enabled or self.kb2joy_capture_mode:
            return True
        
        try:
            # Update activity timestamp
            self.kb2joy_last_activity = time.time()
            
            # Convert key to string representation
            key_str = self._key_to_string(key)
            
            # Debug logging if enabled
            if self.kb2joy_debug_mode:
                self._add_log(f"🔍 Pynput: {key_str}")
            
            # Check if this key is mapped
            for xbox_button, mapped_input in self.kb2joy_mappings.items():
                if mapped_input == key_str:
                    # Send Xbox controller input
                    button = self.virtual_controller.get_button_from_string(xbox_button)
                    if button:
                        self.virtual_controller.press_button(button, duration=0.1)
                        
                        # Check if user wants experimental suppression
                        if (self.kb2joy_suppression_active and 
                            hasattr(self, 'kb2joy_advanced_suppress_var') and 
                            self.kb2joy_advanced_suppress_var and
                            self.kb2joy_advanced_suppress_var.get()):
                            
                            self._add_log(f"KB2JOY: {key_str} -> {xbox_button} [EXPERIMENTAL SUPPRESSION]")
                            # WARNING: This may break the listener!
                            return False
                        else:
                            # Safe mode - always allow original input through
                            if self.kb2joy_suppression_active:
                                self._add_log(f"KB2JOY: {key_str} -> {xbox_button} [CONVERTED + PASS-THROUGH]")
                            else:
                                self._add_log(f"KB2JOY: {key_str} -> {xbox_button} [CONVERTED]")
                            return True
                    break
            
            # Key not mapped - always allow it through
            if self.kb2joy_debug_mode:
                self._add_log(f"✅ Pynput: {key_str} [UNMAPPED - ALLOWED]")
            return True
            
        except Exception as e:
            self._add_log(f"Error in monitored handler: {e}")
            # On error, switch to safe mode
            self._switch_to_safe_mode()
            return True
    
    def _on_kb2joy_key_press_with_suppression(self, key):
        """Handle keyboard key press events WITH suppression. Uses a safer approach."""
        if not self.kb2joy_enabled or self.kb2joy_capture_mode:
            return True  # Allow input to pass through, keep listener active
        
        try:
            # Convert key to string representation
            key_str = self._key_to_string(key)
            
            # Check if this key is mapped to any Xbox button
            is_mapped = False
            for xbox_button, mapped_input in self.kb2joy_mappings.items():
                if mapped_input == key_str:
                    is_mapped = True
                    # Send Xbox controller input
                    button = self.virtual_controller.get_button_from_string(xbox_button)
                    if button:
                        self.virtual_controller.press_button(button, duration=0.1)
                        
                        # Check if we should suppress the input
                        if self.kb2joy_suppress_enabled:
                            self._add_log(f"KB2JOY: {key_str} -> {xbox_button} [ATTEMPTING BLOCK]")
                            # Try to suppress but be prepared to fall back
                            try:
                                return False  # Attempt suppression
                            except:
                                # If suppression fails, log and continue without suppression
                                self._add_log(f"KB2JOY: Suppression failed for {key_str}, switching to fallback mode")
                                self._switch_to_fallback_mode()
                                return True
                        else:
                            self._add_log(f"KB2JOY: {key_str} -> {xbox_button} [CONVERTED]")
                            return True   # Allow mapped keys to pass through
                    break
            
            # Key not mapped - always allow it to pass through
            return True
                    
        except Exception as e:
            self._add_log(f"Error in suppression handler: {e}")
            # On any error, switch to safe fallback mode
            self._switch_to_fallback_mode()
            return True  # Always allow input on error to keep listener alive
    
    def _start_kb2joy_fallback_mode(self):
        """Start KB2JOY in fallback mode without suppression."""
        try:
            self._add_log("🔄 Starting KB2JOY in fallback mode (no suppression)")
            
            # Stop any existing listeners
            self._stop_kb2joy()
            
            # Create non-suppressing listeners
            self.kb2joy_listener = keyboard.Listener(
                on_press=self._on_kb2joy_key_press,
                on_release=self._on_kb2joy_key_release,
                suppress=False
            )
            
            self.kb2joy_mouse_listener = mouse.Listener(
                on_click=self._on_kb2joy_mouse_click,
                on_scroll=self._on_kb2joy_mouse_scroll,
                suppress=False
            )
            
            # Start listeners
            self.kb2joy_listener.start()
            self.kb2joy_mouse_listener.start()
            
            self.kb2joy_enabled = True
            self.kb2joy_suppress_enabled = False  # Force disable suppression
            self.kb2joy_status_label.configure(text="Status: Active - Conversion only (no suppression)")
            self._add_log("KB2JOY fallback mode active - keys will be converted but not suppressed")
            
        except Exception as e:
            self._add_log(f"Error starting KB2JOY fallback mode: {e}")
            self.show_centered_messagebox("Error", f"Failed to start KB2JOY: {e}", "error")
            self.kb2joy_enabled_var.set(False)
    
    def _test_suppression_working(self):
        """Test if suppression is actually working."""
        try:
            if not self.kb2joy_enabled:
                return
                
            # Check if listener is still running
            if self.kb2joy_listener and self.kb2joy_listener.running:
                self._add_log("✅ KB2JOY suppression mode is stable and running")
                if self.kb2joy_suppress_enabled:
                    self._add_log("💡 Test suppression: Map a key and press it in Notepad")
                    self._add_log("💡 If the key still appears in Notepad, run as Administrator")
            else:
                self._add_log("⚠️ KB2JOY listener stopped - restarting in fallback mode")
                self._start_kb2joy_fallback_mode()
                
        except Exception as e:
            self._add_log(f"Error testing suppression: {e}")
            self._start_kb2joy_fallback_mode()
    
    def _switch_to_fallback_mode(self):
        """Switch to fallback mode when suppression fails during operation."""
        try:
            if not self.kb2joy_enabled:
                return
                
            self._add_log("⚠️ Suppression failed during operation - switching to fallback mode")
            
            # Restart in fallback mode
            self.root.after(100, self._restart_in_fallback_mode)
            
        except Exception as e:
            self._add_log(f"Error switching to fallback mode: {e}")
    
    def _restart_in_fallback_mode(self):
        """Restart KB2JOY in fallback mode."""
        try:
            # Store current state
            was_enabled = self.kb2joy_enabled
            current_mappings = self.kb2joy_mappings.copy()
            
            # Stop current listeners
            self._stop_kb2joy()
            
            # Wait a moment
            time.sleep(0.1)
            
            # Restart in fallback mode if it was enabled
            if was_enabled:
                self.kb2joy_mappings = current_mappings  # Restore mappings
                self._start_kb2joy_fallback_mode()
                
        except Exception as e:
            self._add_log(f"Error restarting in fallback mode: {e}")
    
    def _on_kb2joy_key_release(self, key):
        """Handle keyboard key release events."""
        # For now, we use press_button with duration, so no release handling needed
        # Always return True to keep listener active
        return
    
    def _on_kb2joy_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events. Returns False to suppress input if converted."""
        if not self.kb2joy_enabled or self.kb2joy_capture_mode or not pressed:
            return True  # Allow input to pass through
        
        try:
            # Convert mouse button to string
            button_str = f"mouse_{button.name.lower()}"
            
            # Check if this mouse button is mapped
            for xbox_button, mapped_input in self.kb2joy_mappings.items():
                if mapped_input == button_str:
                    # Send Xbox controller input
                    controller_button = self.virtual_controller.get_button_from_string(xbox_button)
                    if controller_button:
                        self.virtual_controller.press_button(controller_button, duration=0.1)
                        
                        # For mouse, we always allow the input to pass through to avoid losing mouse control
                        # We only convert to controller input but don't block the original
                        self._add_log(f"KB2JOY: {button_str} -> {xbox_button} [MOUSE CONVERTED - original input preserved]")
                        return True  # Always allow mouse input to pass through for safety
            
            # Mouse button not mapped, allow it to pass through
            return True
                        
        except Exception as e:
            self._add_log(f"Error processing mouse click: {e}")
            return True  # Allow input on error
    
    def _start_suppression_monitoring(self):
        """Start periodic monitoring of suppression system"""
        if hasattr(self, 'kb2joy_monitor_timer') and self.kb2joy_monitor_timer:
            self.root.after_cancel(self.kb2joy_monitor_timer)
        
        self._check_suppression_health()
    
    def _check_suppression_health(self):
        """Check if suppression system is still working"""
        if not self.kb2joy_enabled or not self.kb2joy_suppression_active:
            return
        
        current_time = time.time()
        time_since_activity = current_time - self.kb2joy_last_activity
        
        # If no activity for 30+ seconds and we think suppression is active,
        # the listener might have died
        if time_since_activity > 30:
            self._add_log(f"⚠️ No KB2JOY activity for {time_since_activity:.1f}s, checking health...")
            
            # Check if listeners are still running
            if (not hasattr(self.kb2joy_listener, 'running') or 
                not self.kb2joy_listener.running):
                self._add_log("❌ Keyboard listener stopped, switching to safe mode")
                self._switch_to_safe_mode()
                return
        
        # Schedule next check
        self.kb2joy_monitor_timer = self.root.after(5000, self._check_suppression_health)
    
    def _switch_to_safe_mode(self):
        """Switch to safe mode (no suppression) when issues detected"""
        try:
            self._add_log("🛡️ Switching to safe mode due to suppression issues")
            
            # Stop current system
            self._stop_kb2joy()
            
            # Uncheck suppression option
            self.suppress_original_var.set(False)
            
            # Update status
            self.status_label.configure(text="KB2JOY Active (Safe Mode - Suppression Disabled)")
            
            # Start without suppression
            self._start_kb2joy_basic()
            
        except Exception as e:
            self._add_log(f"Error switching to safe mode: {e}")
            self.status_label.configure(text=f"KB2JOY Error: {str(e)}")
    
    def _start_kb2joy_basic(self):
        """Start basic KB2JOY without suppression"""
        try:
            # Start keyboard listener
            self.kb2joy_listener = keyboard.Listener(
                on_press=self._on_kb2joy_key_press
            )
            self.kb2joy_listener.start()
            
            # Start mouse listener
            self.kb2joy_mouse_listener = mouse.Listener(
                on_click=self._on_kb2joy_mouse_click
            )
            self.kb2joy_mouse_listener.start()
            
            # Mark as active but suppression as inactive
            self.kb2joy_enabled = True
            self.kb2joy_suppression_active = False
            
            self._add_log("✅ KB2JOY started in basic mode (no suppression)")
            
        except Exception as e:
            self._add_log(f"Error starting basic KB2JOY: {e}")
            raise
    
    def _install_keyboard_hook(self):
        """Install Windows keyboard hook for proper key suppression."""
        if not WINDOWS_HOOK_AVAILABLE:
            self._add_log("❌ Windows hook not available - suppression will be limited")
            return False
            
        try:
            # Define Windows constants
            WH_KEYBOARD_LL = 13
            WM_KEYDOWN = 0x0100
            WM_SYSKEYDOWN = 0x0104
            
            # Store reference to self for the hook procedure
            app_ref = self
            
            # Define hook procedure with safer access to app state
            def low_level_keyboard_proc(nCode, wParam, lParam):
                try:
                    # Only process if we should and if suppression is active
                    if (nCode >= 0 and 
                        hasattr(app_ref, 'kb2joy_suppression_active') and 
                        app_ref.kb2joy_suppression_active and
                        wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)):
                        
                        # Get virtual key code from KBDLLHOOKSTRUCT safely
                        vk_code = ctypes.c_ulong.from_address(lParam).value
                        
                        # Debug logging if enabled
                        if (hasattr(app_ref, 'kb2joy_debug_mode') and 
                            app_ref.kb2joy_debug_mode and
                            hasattr(app_ref, 'kb2joy_suppressed_keys')):
                            app_ref._add_log(f"🔍 Hook: VK={vk_code}, mapped_keys={list(app_ref.kb2joy_suppressed_keys)}")
                        
                        # Check if this specific key should be suppressed
                        if (hasattr(app_ref, 'kb2joy_suppressed_keys') and 
                            vk_code in app_ref.kb2joy_suppressed_keys):
                            if hasattr(app_ref, '_add_log'):
                                app_ref._add_log(f"🛡️ Hook suppressed mapped key VK: {vk_code}")
                            return 1  # Suppress ONLY this specific key
                        
                        # Key is NOT in our suppressed set - allow it through
                        if (hasattr(app_ref, 'kb2joy_debug_mode') and 
                            app_ref.kb2joy_debug_mode and
                            hasattr(app_ref, '_add_log')):
                            app_ref._add_log(f"✅ Hook allowed unmapped key VK: {vk_code}")
                
                except Exception as e:
                    # On any error, allow the key through and log error
                    if hasattr(app_ref, '_add_log'):
                        app_ref._add_log(f"Hook error: {e}")
                
                # Call next hook in chain for all non-suppressed keys
                return ctypes.windll.user32.CallNextHookExW(None, nCode, wParam, lParam)
            
            # Convert to correct function pointer type
            HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
            self.kb2joy_hook_proc = HOOKPROC(low_level_keyboard_proc)
            
            # Install the hook
            self.kb2joy_hook = ctypes.windll.user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                self.kb2joy_hook_proc,
                ctypes.windll.kernel32.GetModuleHandleW(None),
                0
            )
            
            if self.kb2joy_hook:
                self.kb2joy_hook_installed = True
                self._add_log("✅ Windows keyboard hook installed successfully")
                self._add_log(f"🔧 Hook will suppress VK codes: {list(self.kb2joy_suppressed_keys)}")
                return True
            else:
                self._add_log("❌ Failed to install Windows keyboard hook")
                return False
                
        except Exception as e:
            self._add_log(f"❌ Error installing keyboard hook: {e}")
            return False
    
    def _uninstall_keyboard_hook(self):
        """Uninstall Windows keyboard hook."""
        if self.kb2joy_hook_installed and self.kb2joy_hook:
            try:
                ctypes.windll.user32.UnhookWindowsHookExW(self.kb2joy_hook)
                self.kb2joy_hook = None
                self.kb2joy_hook_installed = False
                self._add_log("🔓 Windows keyboard hook uninstalled")
            except Exception as e:
                self._add_log(f"Error uninstalling keyboard hook: {e}")
    
    def _key_to_vk_code(self, key_str):
        """Convert key string to Windows VK code."""
        # Common key mappings
        vk_map = {
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
            'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
            'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
            's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
            'y': 0x59, 'z': 0x5A,
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
            '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
            'space': 0x20, 'enter': 0x0D, 'tab': 0x09, 'shift': 0x10,
            'ctrl': 0x11, 'alt': 0x12, 'escape': 0x1B, 'backspace': 0x08,
            'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
            'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
            'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
            'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
        }
        
        return vk_map.get(key_str.lower())
    
    def _update_suppressed_keys(self):
        """Update the set of keys that should be suppressed by the Windows hook."""
        old_keys = self.kb2joy_suppressed_keys.copy()
        self.kb2joy_suppressed_keys.clear()
        
        self._add_log(f"🔄 Updating suppressed keys - mappings: {len(self.kb2joy_mappings)}, suppression_active: {self.kb2joy_suppression_active}")
        
        if self.kb2joy_suppression_active:
            # Debug: Show all current mappings
            for xbox_button, mapped_input in self.kb2joy_mappings.items():
                self._add_log(f"📝 Mapping: {xbox_button} ← {mapped_input}")
            
            keyboard_mappings = 0
            for xbox_button, mapped_input in self.kb2joy_mappings.items():
                # Only suppress keyboard keys (not mouse)
                if not mapped_input.startswith('mouse_'):
                    keyboard_mappings += 1
                    vk_code = self._key_to_vk_code(mapped_input)
                    if vk_code:
                        self.kb2joy_suppressed_keys.add(vk_code)
                        self._add_log(f"🔐 Will suppress '{mapped_input}' (VK: {vk_code}) → {xbox_button}")
                    else:
                        self._add_log(f"⚠️ Could not get VK code for '{mapped_input}' - check key name format")
                else:
                    self._add_log(f"🖱️ Skipping mouse input: {mapped_input} → {xbox_button}")
            
            self._add_log(f"� Summary: {keyboard_mappings} keyboard mappings, {len(self.kb2joy_suppressed_keys)} VK codes to suppress")
            self._add_log(f"📋 VK codes to suppress: {sorted(list(self.kb2joy_suppressed_keys))}")
        else:
            self._add_log("🔓 Suppression inactive - no keys will be suppressed")
    
    def _on_kb2joy_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events. Returns False to suppress input if converted."""
        if not self.kb2joy_enabled or self.kb2joy_capture_mode:
            return True  # Allow input to pass through
        
        try:
            # Convert scroll to string
            if dy > 0:
                scroll_str = "scroll_up"
            else:
                scroll_str = "scroll_down"
            
            # Check if scroll is mapped
            for xbox_button, mapped_input in self.kb2joy_mappings.items():
                if mapped_input == scroll_str:
                    controller_button = self.virtual_controller.get_button_from_string(xbox_button)
                    if controller_button:
                        self.virtual_controller.press_button(controller_button, duration=0.1)
                        
                        # For mouse scroll, we always allow the input to pass through to avoid losing scroll control
                        # We only convert to controller input but don't block the original
                        self._add_log(f"KB2JOY: {scroll_str} -> {xbox_button} [SCROLL CONVERTED - original input preserved]")
                        return True  # Always allow scroll input to pass through for safety
            
            # Scroll not mapped, allow it to pass through
            return True
                        
        except Exception as e:
            self._add_log(f"Error processing mouse scroll: {e}")
            return True  # Allow input on error
    
    def _key_to_string(self, key):
        """Convert pynput key to string representation."""
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char.lower()
            else:
                # Special keys
                key_name = str(key).replace('Key.', '')
                return key_name.lower()
        except:
            return str(key)
    
    def _capture_input_for_button(self, xbox_button):
        """Capture input for a specific Xbox button."""
        if not PYNPUT_AVAILABLE:
            self.show_centered_messagebox("Error", "pynput library is required", "error")
            return
        
        # Set capture mode
        self.kb2joy_capture_mode = True
        self.current_capture_button = xbox_button
        
        # Update button text
        if xbox_button in self.mapping_widgets:
            self.mapping_widgets[xbox_button]['capture_btn'].configure(text="Press key...")
            self.mapping_widgets[xbox_button]['label'].configure(text="Waiting for input...")
        
        # Show capture dialog
        self._show_capture_dialog(xbox_button)
    
    def _show_capture_dialog(self, xbox_button):
        """Show input capture dialog."""
        # Create capture window
        capture_window = tk.Toplevel(self.root)
        capture_window.title(f"Capture Input for {xbox_button}")
        capture_window.geometry("400x200")
        capture_window.transient(self.root)
        capture_window.grab_set()
        
        # Center dialog
        self.center_dialog_on_main(capture_window)
        
        # Instructions
        instruction_label = tk.Label(capture_window, 
                                    text=f"Press any key or mouse button to map to {xbox_button}\\n\\nPress ESC to cancel",
                                    font=("Arial", 12),
                                    justify="center")
        instruction_label.pack(expand=True, pady=20)
        
        # Status label
        status_label = tk.Label(capture_window, text="Waiting for input...", 
                              font=("Arial", 10), fg="gray")
        status_label.pack(pady=10)
        
        captured_input = None
        
        def on_key_press(key):
            nonlocal captured_input
            try:
                if key == keyboard.Key.esc:
                    capture_window.destroy()
                    return False
                
                captured_input = self._key_to_string(key)
                status_label.configure(text=f"Captured: {captured_input}")
                capture_window.after(500, lambda: capture_window.destroy())
                return False  # Stop listener
            except:
                return True
        
        def on_mouse_click(x, y, button, pressed):
            nonlocal captured_input
            if pressed:
                captured_input = f"mouse_{button.name.lower()}"
                status_label.configure(text=f"Captured: {captured_input}")
                capture_window.after(500, lambda: capture_window.destroy())
                return False
        
        def on_mouse_scroll(x, y, dx, dy):
            nonlocal captured_input
            if dy > 0:
                captured_input = "scroll_up"
            else:
                captured_input = "scroll_down"
            status_label.configure(text=f"Captured: {captured_input}")
            capture_window.after(500, lambda: capture_window.destroy())
            return False
        
        # Create temporary listeners for capture
        temp_kb_listener = keyboard.Listener(on_press=on_key_press)
        temp_mouse_listener = mouse.Listener(on_click=on_mouse_click, on_scroll=on_mouse_scroll)
        
        temp_kb_listener.start()
        temp_mouse_listener.start()
        
        def on_dialog_close():
            temp_kb_listener.stop()
            temp_mouse_listener.stop()
            
            self.kb2joy_capture_mode = False
            
            if captured_input:
                # Save the mapping
                self.kb2joy_mappings[xbox_button] = captured_input
                self._update_mapping_display(xbox_button, captured_input)
                self._add_log(f"Mapped {captured_input} to {xbox_button}")
                
                # Update Windows hook suppressed keys if KB2JOY is active
                if self.kb2joy_enabled and self.kb2joy_suppression_active:
                    self._update_suppressed_keys()
            
            # Reset button text
            if xbox_button in self.mapping_widgets:
                self.mapping_widgets[xbox_button]['capture_btn'].configure(text="Capture")
                if not captured_input:
                    self.mapping_widgets[xbox_button]['label'].configure(text="Not mapped")
        
        capture_window.protocol("WM_DELETE_WINDOW", on_dialog_close)
        capture_window.wait_window()
        on_dialog_close()
    
    def _clear_mapping(self, xbox_button):
        """Clear mapping for a specific Xbox button."""
        if xbox_button in self.kb2joy_mappings:
            del self.kb2joy_mappings[xbox_button]
            self._update_mapping_display(xbox_button, "Not mapped")
            self._add_log(f"Cleared mapping for {xbox_button}")
            
            # Update Windows hook suppressed keys if KB2JOY is active
            if self.kb2joy_enabled and self.kb2joy_suppression_active:
                self._update_suppressed_keys()
    
    def _toggle_kb2joy_debug(self):
        """Toggle KB2JOY debug mode for troubleshooting."""
        self.kb2joy_debug_mode = not self.kb2joy_debug_mode
        if self.kb2joy_debug_mode:
            self._add_log("🐛 KB2JOY debug mode ENABLED - will log all key presses")
            self._add_log(f"📋 Current mappings: {dict(self.kb2joy_mappings)}")
            self._add_log(f"📋 Currently suppressing VK codes: {list(self.kb2joy_suppressed_keys)}")
            # Test key conversion
            test_keys = ['w', 'a', 's', 'd', 'space', 'enter']
            self._add_log("🧪 Key conversion test:")
            for test_key in test_keys:
                vk = self._key_to_vk_code(test_key)
                self._add_log(f"  '{test_key}' -> VK {vk}")
        else:
            self._add_log("🐛 KB2JOY debug mode DISABLED")
    
    def _clear_all_mappings(self):
        """Clear all KB2JOY mappings."""
        if self.show_centered_messagebox("Confirm", "Clear all input mappings?", "question"):
            self.kb2joy_mappings.clear()
            
            # Update all displays
            for button in self.mapping_widgets:
                self._update_mapping_display(button, "Not mapped")
            
            # Update Windows hook suppressed keys if KB2JOY is active
            if self.kb2joy_enabled and self.kb2joy_suppression_active:
                self._update_suppressed_keys()
            
            self._add_log("Cleared all KB2JOY mappings")
    
    def _update_mapping_display(self, xbox_button, input_str):
        """Update the mapping display for a button."""
        if xbox_button in self.mapping_widgets:
            self.mapping_widgets[xbox_button]['label'].configure(text=input_str)
    
    def _save_kb2joy_config(self):
        """Save KB2JOY mappings to configuration."""
        try:
            config_file = "kb2joy_config.json"
            
            config_data = {
                'mappings': self.kb2joy_mappings,
                'enabled': self.kb2joy_enabled,
                'suppress_input': self.kb2joy_suppress_input_var.get() if hasattr(self, 'kb2joy_suppress_input_var') else True
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self._add_log(f"KB2JOY configuration saved to {config_file}")
            self.show_centered_messagebox("Success", "KB2JOY configuration saved successfully", "info")
            
        except Exception as e:
            self._add_log(f"Error saving KB2JOY config: {e}")
            self.show_centered_messagebox("Error", f"Failed to save configuration: {e}", "error")
    
    def _load_kb2joy_config(self):
        """Load KB2JOY mappings from configuration."""
        try:
            config_file = "kb2joy_config.json"
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                self.kb2joy_mappings = config_data.get('mappings', {})
                
                # Load suppress input setting
                suppress_input = config_data.get('suppress_input', True)
                if hasattr(self, 'kb2joy_suppress_input_var'):
                    self.kb2joy_suppress_input_var.set(suppress_input)
                
                # Update displays
                for button, input_str in self.kb2joy_mappings.items():
                    self._update_mapping_display(button, input_str)
                
                self._add_log(f"Loaded {len(self.kb2joy_mappings)} KB2JOY mappings")
                self.show_centered_messagebox("Success", "KB2JOY configuration loaded successfully", "info")
            else:
                self.show_centered_messagebox("Info", "No saved KB2JOY configuration found", "info")
                
        except Exception as e:
            self._add_log(f"Error loading KB2JOY config: {e}")
            self.show_centered_messagebox("Error", f"Failed to load configuration: {e}", "error")
    
    def _export_kb2joy_config(self):
        """Export KB2JOY configuration to chosen file."""
        try:
            filename = self.show_centered_filedialog("save",
                title="Export KB2JOY Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                config_data = {
                    'mappings': self.kb2joy_mappings,
                    'enabled': self.kb2joy_enabled,
                    'suppress_input': self.kb2joy_suppress_input_var.get() if hasattr(self, 'kb2joy_suppress_input_var') else True,
                    'version': '1.0'
                }
                
                with open(filename, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                self._add_log(f"KB2JOY configuration exported to {filename}")
                self.show_centered_messagebox("Success", "Configuration exported successfully", "info")
                
        except Exception as e:
            self._add_log(f"Error exporting KB2JOY config: {e}")
            self.show_centered_messagebox("Error", f"Failed to export configuration: {e}", "error")
    
    def _import_kb2joy_config(self):
        """Import KB2JOY configuration from chosen file."""
        try:
            filename = self.show_centered_filedialog("open",
                title="Import KB2JOY Configuration",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r') as f:
                    config_data = json.load(f)
                
                self.kb2joy_mappings = config_data.get('mappings', {})
                
                # Load suppress input setting
                suppress_input = config_data.get('suppress_input', True)
                if hasattr(self, 'kb2joy_suppress_input_var'):
                    self.kb2joy_suppress_input_var.set(suppress_input)
                
                # Update displays
                for button in self.mapping_widgets:
                    input_str = self.kb2joy_mappings.get(button, "Not mapped")
                    self._update_mapping_display(button, input_str)
                
                self._add_log(f"Imported {len(self.kb2joy_mappings)} KB2JOY mappings from {filename}")
                self.show_centered_messagebox("Success", "Configuration imported successfully", "info")
                
        except Exception as e:
            self._add_log(f"Error importing KB2JOY config: {e}")
            self.show_centered_messagebox("Error", f"Failed to import configuration: {e}", "error")
    
    def _load_kb2joy_mappings(self):
        """Load KB2JOY mappings on startup."""
        try:
            config_file = "kb2joy_config.json"
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                self.kb2joy_mappings = config_data.get('mappings', {})
                
                # Load suppress input setting
                suppress_input = config_data.get('suppress_input', True)
                if hasattr(self, 'kb2joy_suppress_input_var'):
                    self.kb2joy_suppress_input_var.set(suppress_input)
                
                # Update displays
                for button, input_str in self.kb2joy_mappings.items():
                    self._update_mapping_display(button, input_str)
                
                self._add_log(f"Loaded {len(self.kb2joy_mappings)} saved KB2JOY mappings")
                
        except Exception as e:
            self._add_log(f"Note: No saved KB2JOY mappings found ({e})")
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = StumbleBotApp()
    app.run()