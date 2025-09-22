"""
Xbox Remote Play Bot
A modern bot for Xbox Remote Play that simulates Xbox controller inputs
with image-based recognition and a user-friendly GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
from typing import Dict, List, Tuple, Optional
import cv2
import numpy as np
import pyautogui
import pygetwindow
from PIL import Image, ImageTk
import logging
import keyboard

# Import our custom modules
from xbox_controller import create_controller
from image_recognition import ImageRecognizer, GameStateDetector
from bot_logic import StumbleGuysBot, BotOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XboxRemoteBot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Xbox Remote Play Bot")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Bot state
        self.running = False
        self.bot_thread = None
        self.game_window = None
        
        # Configuration
        self.config_file = "bot_config.json"
        self.templates_dir = "templates"
        self.config = self.load_config()
        
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize components
        self.controller = None
        self.image_recognizer = ImageRecognizer(self.templates_dir)
        self.state_detector = None
        self.bot = None
        self.orchestrator = None
        
        # Global hotkey state
        self.global_hotkey_active = False
        
        self.setup_ui()
        self.update_status()
        self.setup_global_hotkeys()
        
    def setup_ui(self):
        """Setup the main UI with tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.run_frame = ttk.Frame(self.notebook)
        self.config_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.run_frame, text="Run Bot")
        self.notebook.add(self.config_frame, text="Configuration")
        
        self.setup_run_tab()
        self.setup_config_tab()
        
    def setup_run_tab(self):
        """Setup the Run tab interface"""
        # Main controls frame
        controls_frame = ttk.LabelFrame(self.run_frame, text="Bot Controls", padding=10)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        # Window selection
        window_frame = ttk.Frame(controls_frame)
        window_frame.pack(fill='x', pady=5)
        
        ttk.Label(window_frame, text="Target Window:").pack(side='left')
        self.window_var = tk.StringVar(value=self.config.get('window_title', 'Xbox'))
        self.window_entry = ttk.Entry(window_frame, textvariable=self.window_var, width=30)
        self.window_entry.pack(side='left', padx=5)
        
        ttk.Button(window_frame, text="Detect", command=self.detect_window).pack(side='left', padx=5)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Bot", command=self.start_bot)
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Bot", command=self.stop_bot, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        self.test_controller_button = ttk.Button(button_frame, text="Test Controller", command=self.test_controller)
        self.test_controller_button.pack(side='left', padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.run_frame, text="Status", padding=10)
        status_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Status text widget
        self.status_text = tk.Text(status_frame, height=15, wrap='word')
        scrollbar = ttk.Scrollbar(status_frame, orient='vertical', command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Settings frame
        settings_frame = ttk.LabelFrame(self.run_frame, text="Settings", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # Delay settings
        delay_frame = ttk.Frame(settings_frame)
        delay_frame.pack(fill='x')
        
        ttk.Label(delay_frame, text="Check Interval (s):").pack(side='left')
        self.delay_var = tk.DoubleVar(value=self.config.get('check_interval', 1.5))
        delay_spin = ttk.Spinbox(delay_frame, from_=0.5, to=10.0, increment=0.1, 
                                textvariable=self.delay_var, width=10)
        delay_spin.pack(side='left', padx=5)
        
        # Window checking option
        window_check_frame = ttk.Frame(settings_frame)
        window_check_frame.pack(fill='x', pady=5)
        
        self.skip_window_check_var = tk.BooleanVar(value=self.config.get('skip_window_check', False))
        ttk.Checkbutton(window_check_frame, text="Skip window activity check (for debugging)", 
                       variable=self.skip_window_check_var).pack(side='left')
        
    def setup_config_tab(self):
        """Setup the Configuration tab interface"""
        # Instructions frame
        instructions_frame = ttk.LabelFrame(self.config_frame, text="Instructions", padding=10)
        instructions_frame.pack(fill='x', padx=10, pady=5)
        
        instructions = """
1. Click 'Capture Template' for each game state you want to detect
2. Position your cursor over the target button/element
3. Press F9 anywhere (global hotkey) to capture a screenshot around the cursor
4. Adjust the template name and confidence threshold
5. Save the configuration when done

Note: F9 works globally (even when this window is not focused)
F10 can be used for emergency stop when bot is running
        """
        ttk.Label(instructions_frame, text=instructions, justify='left').pack()
        
        # Template capture frame
        capture_frame = ttk.LabelFrame(self.config_frame, text="Template Capture", padding=10)
        capture_frame.pack(fill='x', padx=10, pady=5)
        
        # Template name
        name_frame = ttk.Frame(capture_frame)
        name_frame.pack(fill='x', pady=5)
        
        ttk.Label(name_frame, text="Template Name:").pack(side='left')
        self.template_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.template_name_var, width=30).pack(side='left', padx=5)
        
        # Confidence threshold
        conf_frame = ttk.Frame(capture_frame)
        conf_frame.pack(fill='x', pady=5)
        
        ttk.Label(conf_frame, text="Confidence (0.1-1.0):").pack(side='left')
        self.confidence_var = tk.DoubleVar(value=0.8)
        ttk.Spinbox(conf_frame, from_=0.1, to=1.0, increment=0.05, 
                   textvariable=self.confidence_var, width=10).pack(side='left', padx=5)
        
        # Capture button
        ttk.Button(capture_frame, text="Capture Template (F9)", 
                  command=self.start_template_capture).pack(pady=10)
        
        # Templates list frame
        list_frame = ttk.LabelFrame(self.config_frame, text="Saved Templates", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Templates treeview
        columns = ('Name', 'Confidence', 'Size', 'Created')
        self.templates_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        
        for col in columns:
            self.templates_tree.heading(col, text=col)
            self.templates_tree.column(col, width=100)
            
        self.templates_tree.pack(fill='both', expand=True)
        
        # Template management buttons
        template_buttons = ttk.Frame(list_frame)
        template_buttons.pack(fill='x', pady=5)
        
        ttk.Button(template_buttons, text="Delete Selected", 
                  command=self.delete_template).pack(side='left', padx=5)
        ttk.Button(template_buttons, text="Test Template", 
                  command=self.test_template).pack(side='left', padx=5)
        
        # Configuration save/load
        config_buttons = ttk.Frame(self.config_frame)
        config_buttons.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(config_buttons, text="Save Config", command=self.save_config).pack(side='left', padx=5)
        ttk.Button(config_buttons, text="Load Config", command=self.load_config_file).pack(side='left', padx=5)
        
        # Load existing templates
        self.refresh_templates_list()
        
    def load_config(self) -> Dict:
        """Load configuration from file"""
        default_config = {
            'window_title': 'Xbox',
            'check_interval': 1.5,
            'templates': {},
            'controller_settings': {
                'stick_deadzone': 0.1,
                'trigger_threshold': 0.5
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            
        return default_config
        
    def save_config(self):
        """Save current configuration to file"""
        try:
            self.config['window_title'] = self.window_var.get()
            self.config['check_interval'] = self.delay_var.get()
            self.config['skip_window_check'] = self.skip_window_check_var.get()
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            self.log_status("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved!")
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            messagebox.showerror("Error", f"Failed to save config: {e}")
            
    def load_config_file(self):
        """Load configuration from a selected file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.config = json.load(f)
                    
                # Update UI
                self.window_var.set(self.config.get('window_title', 'Xbox'))
                self.delay_var.set(self.config.get('check_interval', 1.5))
                
                self.refresh_templates_list()
                self.log_status(f"Configuration loaded from {filename}")
                
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                messagebox.showerror("Error", f"Failed to load config: {e}")
                
    def setup_global_hotkeys(self):
        """Setup global hotkeys using keyboard library"""
        try:
            # Register F9 for template capture
            keyboard.add_hotkey('f9', self.on_f9_pressed)
            
            # Register F10 for emergency stop
            keyboard.add_hotkey('f10', self.emergency_stop)
            
            self.global_hotkey_active = True
            logger.info("Global hotkeys registered: F9 (capture), F10 (emergency stop)")
            
        except Exception as e:
            logger.error(f"Failed to register global hotkeys: {e}")
            self.log_status(f"Warning: Global hotkeys not available: {e}")
            self.global_hotkey_active = False
        
    def start_template_capture(self):
        """Start template capture mode"""
        if not self.template_name_var.get().strip():
            messagebox.showwarning("Warning", "Please enter a template name first")
            return
            
        self.capture_mode = True
        if self.global_hotkey_active:
            self.log_status("Template capture mode activated. Press F9 anywhere to capture...")
        else:
            self.log_status("Template capture mode activated. Click 'Capture Now' to capture...")
            # Add a direct capture button as fallback
            self.show_capture_fallback_button()
        
    def capture_template(self, event=None):
        """Capture template around cursor position"""
        if not self.capture_mode:
            return
            
        if not self.template_name_var.get().strip():
            self.log_status("Error: No template name specified")
            return
            
        try:
            # Get cursor position
            cursor_x, cursor_y = pyautogui.position()
            
            # Capture area around cursor (100x100 pixels)
            capture_size = 100
            left = max(0, cursor_x - capture_size // 2)
            top = max(0, cursor_y - capture_size // 2)
            
            # Take screenshot
            screenshot = pyautogui.screenshot(region=(left, top, capture_size, capture_size))
            
            # Save template
            template_name = self.template_name_var.get().strip()
            template_path = os.path.join(self.templates_dir, f"{template_name}.png")
            screenshot.save(template_path)
            
            # Save template info to config
            if 'templates' not in self.config:
                self.config['templates'] = {}
                
            self.config['templates'][template_name] = {
                'path': template_path,
                'confidence': self.confidence_var.get(),
                'size': (capture_size, capture_size),
                'created': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.log_status(f"Template '{template_name}' captured and saved")
            self.refresh_templates_list()
            
            # Reset capture mode
            self.capture_mode = False
            
        except Exception as e:
            logger.error(f"Error capturing template: {e}")
            self.log_status(f"Error capturing template: {e}")
            
    def on_f9_pressed(self):
        """Global F9 hotkey handler"""
        if self.capture_mode:
            # Schedule template capture in the main thread
            self.root.after(0, self.capture_template_safe)
        else:
            # Show message that capture mode needs to be activated first
            self.root.after(0, lambda: self.log_status("F9 pressed, but capture mode not active. Click 'Capture Template' first."))
            
    def capture_template_safe(self):
        """Thread-safe version of capture_template"""
        try:
            self.capture_template()
        except Exception as e:
            logger.error(f"Error in safe template capture: {e}")
            self.log_status(f"Error capturing template: {e}")
            
    def emergency_stop(self):
        """Emergency stop hotkey handler"""
        if self.running:
            self.root.after(0, self.stop_bot)
            self.root.after(0, lambda: self.log_status("Emergency stop activated (F10)"))
            
    def show_capture_fallback_button(self):
        """Show fallback capture button when global hotkeys don't work"""
        # This could add a temporary "Capture Now" button
        # For now, just log the instruction
        self.log_status("Global hotkeys unavailable. Use 'Capture Template' button instead.")
            
    def refresh_templates_list(self):
        """Refresh the templates list in the UI"""
        # Clear existing items
        for item in self.templates_tree.get_children():
            self.templates_tree.delete(item)
            
        # Add templates from config
        for name, info in self.config.get('templates', {}).items():
            self.templates_tree.insert('', 'end', text=name, values=(
                name,
                info.get('confidence', 0.8),
                f"{info.get('size', [0, 0])[0]}x{info.get('size', [0, 0])[1]}",
                info.get('created', 'Unknown')
            ))
            
    def delete_template(self):
        """Delete selected template"""
        selected = self.templates_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a template to delete")
            return
            
        for item in selected:
            template_name = self.templates_tree.item(item)['text']
            
            # Remove from config
            if template_name in self.config.get('templates', {}):
                template_info = self.config['templates'][template_name]
                
                # Delete file
                try:
                    if os.path.exists(template_info['path']):
                        os.remove(template_info['path'])
                except Exception as e:
                    logger.error(f"Error deleting template file: {e}")
                    
                # Remove from config
                del self.config['templates'][template_name]
                
            # Remove from tree
            self.templates_tree.delete(item)
            
        self.log_status(f"Template '{template_name}' deleted")
        
    def test_template(self):
        """Test selected template against current screen"""
        selected = self.templates_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a template to test")
            return
            
        template_name = self.templates_tree.item(selected[0])['text']
        
        if template_name not in self.config.get('templates', {}):
            messagebox.showerror("Error", "Template not found in configuration")
            return
            
        try:
            # Load template
            template_info = self.config['templates'][template_name]
            template = cv2.imread(template_info['path'])
            
            if template is None:
                messagebox.showerror("Error", "Could not load template image")
                return
                
            # Take current screenshot
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            confidence = template_info.get('confidence', 0.8)
            
            if max_val >= confidence:
                self.log_status(f"Template '{template_name}' FOUND with confidence {max_val:.3f} at {max_loc}")
                messagebox.showinfo("Test Result", f"Template found!\nConfidence: {max_val:.3f}\nPosition: {max_loc}")
            else:
                self.log_status(f"Template '{template_name}' NOT FOUND (max confidence: {max_val:.3f})")
                messagebox.showinfo("Test Result", f"Template not found.\nMax confidence: {max_val:.3f}\nRequired: {confidence}")
                
        except Exception as e:
            logger.error(f"Error testing template: {e}")
            messagebox.showerror("Error", f"Failed to test template: {e}")
            
    def detect_window(self):
        """Auto-detect Xbox Remote Play window with selection dialog"""
        try:
            windows = pygetwindow.getAllWindows()
            
            # Filter windows by Xbox-related keywords
            xbox_keywords = ['xbox', 'remote play', 'game streaming', 'cloud gaming']
            xbox_windows = []
            
            for window in windows:
                title_lower = window.title.lower()
                if any(keyword in title_lower for keyword in xbox_keywords) and window.title.strip():
                    # Skip minimized or very small windows
                    if window.width > 100 and window.height > 100:
                        xbox_windows.append(window)
            
            if not xbox_windows:
                self.log_status("No Xbox-related windows found")
                messagebox.showinfo("Detection", "No Xbox-related windows found. Make sure Xbox Remote Play is running.")
                return
                
            if len(xbox_windows) == 1:
                # Only one window found, use it directly
                selected_window = xbox_windows[0]
                self.window_var.set(selected_window.title)
                self.log_status(f"Auto-detected window: {selected_window.title}")
            else:
                # Multiple windows found, show selection dialog
                selected_window = self.show_window_selection_dialog(xbox_windows)
                if selected_window:
                    self.window_var.set(selected_window.title)
                    self.log_status(f"Selected window: {selected_window.title}")
                else:
                    self.log_status("Window selection cancelled")
                
        except Exception as e:
            logger.error(f"Error detecting window: {e}")
            self.log_status(f"Error detecting window: {e}")
            
    def show_window_selection_dialog(self, windows):
        """Show dialog to select from multiple Xbox windows"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Xbox Window")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        selected_window = None
        
        # Instructions
        instructions = ttk.Label(dialog, text="Multiple Xbox-related windows found. Please select one:")
        instructions.pack(pady=10)
        
        # Create listbox with scrollbar
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        listbox = tk.Listbox(list_frame, selectmode='single')
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Add windows to listbox with detailed info
        for i, window in enumerate(windows):
            # Format: "Title | Size: WxH | Visible: Yes/No"
            try:
                visible = "Yes" if window.visible else "No"
                display_text = f"{window.title} | Size: {window.width}x{window.height} | Visible: {visible}"
                listbox.insert(i, display_text)
            except:
                listbox.insert(i, f"{window.title} | (Info unavailable)")
        
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Select first item by default
        if windows:
            listbox.selection_set(0)
            
        # Add window info display
        info_frame = ttk.LabelFrame(dialog, text="Window Details", padding=5)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        info_text = tk.Text(info_frame, height=4, wrap='word')
        info_text.pack(fill='x')
        
        def update_info(event=None):
            """Update window info display"""
            selection = listbox.curselection()
            if selection:
                window = windows[selection[0]]
                try:
                    info = f"Title: {window.title}\n"
                    info += f"Size: {window.width} x {window.height}\n"
                    info += f"Position: ({window.left}, {window.top})\n"
                    info += f"Visible: {'Yes' if window.visible else 'No'}\n"
                    info += f"Active: {'Yes' if window.isActive else 'No'}"
                except:
                    info = f"Title: {window.title}\n(Additional info unavailable)"
                    
                info_text.delete('1.0', 'end')
                info_text.insert('1.0', info)
        
        listbox.bind('<<ListboxSelect>>', update_info)
        update_info()  # Show info for first item
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def on_select():
            nonlocal selected_window
            selection = listbox.curselection()
            if selection:
                selected_window = windows[selection[0]]
                dialog.destroy()
            else:
                messagebox.showwarning("Warning", "Please select a window")
                
        def on_refresh():
            """Refresh the window list"""
            dialog.destroy()
            # Call detect_window again to refresh
            self.root.after(100, self.detect_window)
            
        def on_cancel():
            dialog.destroy()
            
        ttk.Button(button_frame, text="Select", command=on_select).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Refresh", command=on_refresh).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side='left', padx=5)
        
        # Handle double-click
        def on_double_click(event):
            on_select()
            
        listbox.bind('<Double-Button-1>', on_double_click)
        
        # Handle Enter key
        def on_enter(event):
            on_select()
            
        dialog.bind('<Return>', on_enter)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return selected_window
        
    def test_controller(self):
        """Test controller functionality"""
        try:
            self.log_status("Testing controller functionality...")
            
            # Create a test controller
            from xbox_controller import create_controller
            test_controller = create_controller()
            
            if hasattr(test_controller, 'test_input'):
                if test_controller.test_input():
                    self.log_status("Controller test PASSED - inputs should work")
                else:
                    self.log_status("Controller test FAILED - inputs may not work")
            
            # Test some button presses
            self.log_status("Testing button presses...")
            
            # Test A button
            if hasattr(test_controller, 'press_a'):
                result = test_controller.press_a(0.1)
                self.log_status(f"A button test: {'SUCCESS' if result else 'FAILED'}")
            
            # Test movement
            if hasattr(test_controller, 'simulate_random_movement'):
                self.log_status("Testing movement simulation...")
                test_controller.simulate_random_movement(1.0)
                self.log_status("Movement test completed")
            
            self.log_status("Controller test completed - check logs for details")
            
        except Exception as e:
            logger.error(f"Error testing controller: {e}")
            self.log_status(f"Controller test error: {e}")
        
    def is_window_valid(self, window) -> bool:
        """Check if window is valid and accessible (more robust than isActive)"""
        try:
            if not window:
                return False
                
            # Try to access basic window properties
            title = window.title
            width = window.width
            height = window.height
            left = window.left
            top = window.top
            
            # Check if window has reasonable dimensions
            if width < 100 or height < 100:
                return False
                
            # Check if window is visible (this is more reliable than isActive)
            try:
                visible = window.visible
                if not visible:
                    return False
            except:
                # If we can't check visibility, assume it's okay if other checks passed
                pass
                
            # Window passed all checks
            return True
            
        except Exception as e:
            logger.debug(f"Window validation failed: {e}")
            return False
            
    def start_bot(self):
        """Start the bot"""
        if self.running:
            return
            
        # Validate configuration
        if not self.config.get('templates'):
            messagebox.showwarning("Warning", "No templates configured. Please configure templates first.")
            return
            
        try:
            # Find target window
            window_title = self.window_var.get()
            windows = pygetwindow.getWindowsWithTitle(window_title)
            
            if not windows:
                messagebox.showerror("Error", f"Window '{window_title}' not found")
                return
                
            self.game_window = windows[0]
            
            # Initialize controller
            self.log_status("Initializing Xbox controller...")
            self.controller = create_controller()
            
            # Test controller functionality
            if hasattr(self.controller, 'test_input'):
                if self.controller.test_input():
                    self.log_status("Controller test passed")
                else:
                    self.log_status("WARNING: Controller test failed - inputs may not work")
            
            # Initialize state detector
            self.state_detector = GameStateDetector(self.image_recognizer, self.config)
            
            # Initialize bot
            self.bot = StumbleGuysBot(self.controller, self.state_detector)
            
            # Initialize orchestrator with update callback
            self.orchestrator = BotOrchestrator(self.bot, self.update_bot_status)
            
            # Start bot thread
            self.running = True
            self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
            self.bot_thread.start()
            
            # Update UI
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.log_status("Bot started successfully")
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            messagebox.showerror("Error", f"Failed to start bot: {e}")
            
    def stop_bot(self):
        """Stop the bot"""
        self.running = False
        
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=2)
            
        # Update UI
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.log_status("Bot stopped")
        
    def bot_loop(self):
        """Main bot execution loop"""
        self.log_status("Bot loop started")
        
        if self.orchestrator:
            self.orchestrator.start()
        
        while self.running:
            try:
                # Check if window is still accessible (unless skip option is enabled)
                if not self.skip_window_check_var.get():
                    if not self.game_window:
                        self.log_status("Game window not found, waiting...")
                        time.sleep(3)
                        continue
                        
                    try:
                        # Check if window still exists and is visible (more reliable than isActive)
                        window_valid = self.is_window_valid(self.game_window)
                        if not window_valid:
                            self.log_status("Game window not accessible, waiting...")
                            time.sleep(3)
                            continue
                    except Exception as e:
                        # Window might have been closed
                        self.log_status(f"Game window error: {e}")
                        time.sleep(3)
                        continue                # Run bot cycle through orchestrator
                if self.orchestrator:
                    status = self.orchestrator.run_bot_cycle(self.game_window)
                    
                    # Log state changes
                    current_state = status.get('current_state', 'unknown')
                    if hasattr(self, 'last_logged_state') and self.last_logged_state != current_state:
                        self.log_status(f"State changed to: {current_state}")
                        self.last_logged_state = current_state
                    elif not hasattr(self, 'last_logged_state'):
                        self.last_logged_state = current_state
                
                # Wait for next check
                time.sleep(self.delay_var.get())
                
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                self.log_status(f"Bot error: {e}")
                time.sleep(2)
                
        if self.orchestrator:
            self.orchestrator.stop()
            
        self.log_status("Bot loop ended")
        
    def update_bot_status(self, status: dict):
        """Callback for bot status updates"""
        try:
            current_state = status.get('current_state', 'unknown')
            stats = status.get('stats', {})
            
            # Update status display with stats
            if stats:
                stats_text = (f"Games: {stats.get('games_played', 0)} | "
                            f"Rewards: {stats.get('rewards_collected', 0)} | "
                            f"Runtime: {stats.get('runtime', 0):.1f}s")
                            
                # Schedule UI update
                self.root.after(0, self._update_stats_display, stats_text)
                
        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
            
    def _update_stats_display(self, stats_text: str):
        """Update stats display in UI thread"""
        # This could be expanded to show stats in a dedicated area
        # For now, we'll just log it
        pass
        
    def log_status(self, message: str):
        """Log a status message to the UI"""
        timestamp = time.strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        # Update UI in thread-safe way
        self.root.after(0, self._update_status_text, log_message)
        logger.info(message)
        
    def _update_status_text(self, message: str):
        """Update status text widget (called from main thread)"""
        self.status_text.insert('end', message)
        self.status_text.see('end')
        
        # Limit text widget size
        lines = int(self.status_text.index('end-1c').split('.')[0])
        if lines > 1000:
            self.status_text.delete('1.0', '500.0')
            
    de