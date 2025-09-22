"""
Main Application GUI

CustomTkinter-based interface with three tabs:
1. Run - Bot control and logging
2. Configuration - Rules and settings
3. Joystick - Manual controller
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import threading
import time
import os
from typing import List, Dict, Optional
import queue
from PIL import Image, ImageTk

from modules.window_manager import WindowManager
from modules.image_detector import ImageDetector
from modules.virtual_controller import VirtualController, XboxButton
from modules.bot_thread import BotThread
from modules.config_manager import ConfigManager


class StumbleBotApp:
    """Main application class with GUI and bot management."""
    
    def __init__(self):
        """Initialize the application."""
        # Initialize modules
        self.window_manager = WindowManager()
        self.image_detector = ImageDetector()
        self.virtual_controller = VirtualController()
        self.config_manager = ConfigManager()
        self.bot_thread = None
        
        # GUI state
        self.log_queue = queue.Queue()
        self.current_rules = []
        self.selected_rule_index = None
        
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
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Create main tab view
        self.tab_view = ctk.CTkTabview(self.root, width=780, height=580)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tab_view.add("Run")
        self.tab_view.add("Configuration")
        self.tab_view.add("Joystick")
        
        # Setup individual tabs
        self._setup_run_tab()
        self._setup_configuration_tab()
        self._setup_joystick_tab()
    
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
        
        # Rules list and controls
        rules_control_frame = ctk.CTkFrame(rules_frame)
        rules_control_frame.pack(fill="x", padx=10, pady=5)
        
        # Rules list container
        rules_list_frame = ctk.CTkFrame(rules_control_frame)
        rules_list_frame.pack(side="left", fill="both", expand=True)
        
        # Rules listbox
        self.rules_listbox = tk.Listbox(rules_list_frame, height=6, font=("Consolas", 10))
        self.rules_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.rules_listbox.bind('<<ListboxSelect>>', self._on_rule_select)
        
        # Template preview frame
        preview_frame = ctk.CTkFrame(rules_control_frame)
        preview_frame.pack(side="right", fill="y", padx=(10, 0))
        
        preview_label = ctk.CTkLabel(preview_frame, text="Template Preview")
        preview_label.pack(pady=(5, 0))
        
        # Preview image label (placeholder)
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
        
        ctk.CTkLabel(self.simple_action_frame, text="Button:", width=120).pack(side="left", padx=5)
        
        available_actions = [button.value for button in XboxButton]
        self.action_combobox = ctk.CTkComboBox(self.simple_action_frame, values=available_actions)
        self.action_combobox.pack(side="left", fill="x", expand=True, padx=5)
        self.action_combobox.set("A")
        
        # Sequence action entry
        self.sequence_action_frame = ctk.CTkFrame(details_frame)
        
        ctk.CTkLabel(self.sequence_action_frame, text="Sequence:", width=120).pack(side="left", padx=5)
        self.sequence_entry = ctk.CTkEntry(self.sequence_action_frame, 
                                          placeholder_text="STICK_UP:2,STICK_LEFT:1.5,STICK_RIGHT:1")
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
                self._add_log
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
            messagebox.showerror("Error", f"Failed to start bot: {e}")
    
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
                debug_info += f"\nTemplate files found: {len(template_files)}\n"
                for template in template_files:
                    debug_info += f"  - {template}\n"
            else:
                debug_info += f"\nTemplates directory not found: {templates_dir}\n"
            
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

2. CHECK RULES:
   - Make sure you have at least one enabled rule
   - Verify template names match actual files
   - Try lowering confidence threshold (0.7-0.8)

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
    
    def _on_rule_select(self, event):
        """Handle rule selection in listbox."""
        selection = self.rules_listbox.curselection()
        if selection:
            self.selected_rule_index = selection[0]
            self._load_rule_to_details(self.selected_rule_index)
            self._update_template_preview(self.selected_rule_index)
    
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
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # Update the preview label
                    self.preview_image_label.configure(
                        image=photo, 
                        text="",
                        fg_color="transparent"
                    )
                    # Keep a reference to prevent garbage collection
                    self.preview_image_label.image = photo
                else:
                    # Template file not found
                    self.preview_image_label.configure(
                        image=None,
                        text=f"Template\n'{rule.template}'\nnot found",
                        fg_color="red"
                    )
                    self.preview_image_label.image = None
            else:
                # No rule selected
                self.preview_image_label.configure(
                    image=None,
                    text="No template\nselected",
                    fg_color="gray20"
                )
                self.preview_image_label.image = None
                
        except Exception as e:
            # Error loading image
            self.preview_image_label.configure(
                image=None,
                text=f"Error loading\ntemplate:\n{str(e)[:20]}...",
                fg_color="red"
            )
            self.preview_image_label.image = None
    
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
            
            # Check if action is a sequence or simple button
            action = rule.action
            if ',' in action and ':' in action:
                # It's a sequence
                self.action_type_var.set("sequence")
                self.sequence_entry.delete(0, "end")
                self.sequence_entry.insert(0, action)
            else:
                # It's a simple button
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
                messagebox.showinfo("Window Detection", f"No windows found with title '{window_title}'")
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
        """Refresh the rules listbox."""
        self.rules_listbox.delete(0, "end")
        self.current_rules = self.config_manager.get_detection_rules()
        
        for rule in self.current_rules:
            # State indicator
            state = "✓ Enabled" if rule.enabled else "✗ Disabled"
            
            # Format: State - Name - Template - Action
            display_text = f"{state} - {rule.name} - {rule.template} - {rule.action}"
            
            self.rules_listbox.insert("end", display_text)
        
        # Clear template preview
        if hasattr(self, 'preview_image_label'):
            self.preview_image_label.configure(
                image=None,
                text="No template\nselected",
                fg_color="gray20"
            )
            self.preview_image_label.image = None
    
    # Rules management methods
    def _add_rule(self):
        """Add a new detection rule."""
        try:
            # Clear detail entries
            self.rule_name_entry.delete(0, "end")
            self.template_name_entry.delete(0, "end")
            self.confidence_slider.set(0.8)
            self.action_combobox.set("A")
            
            # Clear selection
            self.rules_listbox.selection_clear(0, "end")
            self.selected_rule_index = None
            
            self._add_log("Ready to add new rule - fill in details and click Save Rule")
            
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
            
            # Validate sequence format if it's a sequence
            if action_type == "sequence":
                if not self._validate_sequence(action):
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
            if self.selected_rule_index is not None:
                # Update existing rule
                old_rule = self.current_rules[self.selected_rule_index]
                if self.config_manager.update_detection_rule(old_rule.name, template, confidence, action, enabled):
                    # If name changed, we need to remove old and add new
                    if old_rule.name != name:
                        self.config_manager.remove_detection_rule(old_rule.name)
                        self.config_manager.add_detection_rule(name, template, confidence, action, enabled)
                    
                    self._add_log(f"Rule '{name}' updated")
                else:
                    self._add_log(f"Failed to update rule '{name}'")
            else:
                # Add new rule
                if self.config_manager.add_detection_rule(name, template, confidence, action, enabled):
                    self._add_log(f"Rule '{name}' added")
                else:
                    self._add_log(f"Failed to add rule '{name}' (name may already exist)")
                    messagebox.showerror("Error", f"Failed to add rule. Rule name '{name}' may already exist.")
                    return
            
            # Refresh GUI
            self._refresh_rules_list()
            
            # Clear selection
            self.selected_rule_index = None
            
        except Exception as e:
            self._add_log(f"Error saving rule: {e}")
            messagebox.showerror("Error", f"Failed to save rule: {e}")
    
    def _validate_sequence(self, sequence: str) -> bool:
        """Validate sequence format."""
        try:
            if not sequence.strip():
                messagebox.showerror("Invalid Sequence", "Sequence cannot be empty")
                return False
            
            steps = sequence.split(',')
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
            
        except Exception as e:
            messagebox.showerror("Validation Error", f"Error validating sequence: {e}")
            return False
    
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
                messagebox.showerror("No Template Name", "Please enter a template name first")
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
    
    # Configuration management methods
    def _save_config(self):
        """Save current configuration to file."""
        try:
            # Update config from GUI first
            self._save_gui_to_config()
            
            # Ask for filename
            filename = tk.simpledialog.askstring("Save Configuration", 
                                                "Enter configuration name:", 
                                                initialvalue="my_config.json")
            
            if filename:
                # Ensure .json extension
                if not filename.endswith('.json'):
                    filename += '.json'
                
                if self.config_manager.save_config(filename):
                    self._add_log(f"Configuration saved as '{filename}'")
                    messagebox.showinfo("Success", f"Configuration saved as '{filename}'")
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
                messagebox.showinfo("No Configurations", "No configuration files found")
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
                    
                    messagebox.showinfo("Success", f"Configuration loaded from '{selected_file}'")
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
            filename = filedialog.asksaveasfilename(
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
            filename = filedialog.askopenfilename(
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
        """Show available templates for selection."""
        try:
            # Get available templates
            available_templates = []
            templates_dir = "templates"
            
            if os.path.exists(templates_dir):
                for file in os.listdir(templates_dir):
                    if file.endswith('.png'):
                        available_templates.append(file)
            
            if not available_templates:
                messagebox.showinfo("No Templates", "No template files found in templates/ directory")
                return
            
            # Create selection window
            selection_window = tk.Toplevel(self.root)
            selection_window.title("Select Template")
            selection_window.geometry("400x300")
            selection_window.transient(self.root)
            selection_window.grab_set()
            
            tk.Label(selection_window, text="Available Templates:", font=("Arial", 12)).pack(pady=10)
            
            # Listbox for templates
            listbox = tk.Listbox(selection_window, height=10)
            listbox.pack(fill="both", expand=True, padx=20, pady=10)
            
            for template in available_templates:
                listbox.insert("end", template)
            
            selected_template = None
            
            def on_select():
                nonlocal selected_template
                selection = listbox.curselection()
                if selection:
                    selected_template = available_templates[selection[0]]
                    selection_window.destroy()
            
            def on_preview():
                selection = listbox.curselection()
                if selection:
                    template_name = available_templates[selection[0]]
                    self._show_template_preview(template_name)
            
            def on_cancel():
                selection_window.destroy()
            
            # Buttons
            btn_frame = tk.Frame(selection_window)
            btn_frame.pack(pady=10)
            
            tk.Button(btn_frame, text="Select", command=on_select, width=10).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Preview", command=on_preview, width=10).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side="left", padx=5)
            
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
        """Show template preview window."""
        try:
            import cv2
            from PIL import Image, ImageTk
            
            template_path = os.path.join("templates", template_filename)
            
            if not os.path.exists(template_path):
                messagebox.showerror("Template Not Found", f"Template file not found: {template_path}")
                return
            
            # Load template image
            template_cv = cv2.imread(template_path)
            if template_cv is None:
                messagebox.showerror("Error", f"Could not load template: {template_path}")
                return
            
            # Convert BGR to RGB for display
            template_rgb = cv2.cvtColor(template_cv, cv2.COLOR_BGR2RGB)
            
            # Create preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"Template Preview: {template_filename}")
            preview_window.transient(self.root)
            
            # Convert to PhotoImage for display
            pil_image = Image.fromarray(template_rgb)
            
            # Scale image if too large
            max_size = (400, 400)
            pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_image)
            
            # Display image
            image_label = tk.Label(preview_window, image=photo)
            image_label.image = photo  # Keep a reference
            image_label.pack(padx=20, pady=20)
            
            # Info label
            info_text = f"File: {template_filename}\nSize: {template_cv.shape[1]}x{template_cv.shape[0]} pixels"
            info_label = tk.Label(preview_window, text=info_text, font=("Arial", 10))
            info_label.pack(pady=(0, 10))
            
            # Test detection button
            def test_detection():
                preview_window.destroy()
                self._test_template_detection(template_filename)
            
            test_btn = tk.Button(preview_window, text="Test Detection", command=test_detection)
            test_btn.pack(pady=10)
            
            # Close button
            close_btn = tk.Button(preview_window, text="Close", command=preview_window.destroy)
            close_btn.pack(pady=(0, 20))
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error showing preview: {e}")
    
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
    
    def _show_sequence_help(self):
        """Show help for sequence format."""
        help_text = """
=== SEQUENCE FORMAT HELP ===

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

Duration: Time in seconds (decimals allowed)

Examples:
🎮 Joystick movement sequence:
   STICK_UP:2.0,STICK_LEFT:1.5,STICK_RIGHT:1.0

🎮 Jump and move with stick:
   A:0.2,STICK_UP:1.0

🎮 Circle movement:
   STICK_UP:1,STICK_RIGHT:1,STICK_DOWN:1,STICK_LEFT:1

🎮 Complex combo:
   X:0.1,Y:0.1,STICK_DOWN:0.5,A:0.2

Notes:
- Each button is held for the specified duration
- 0.1 second pause between each step
- Sequence executes when template is detected
- Use shorter durations (0.1-0.5s) for quick actions
- Use longer durations (1-3s) for movement
- Stick movements provide analog control vs DPAD digital
"""
        self._add_log(help_text)
    
    def _on_closing(self):
        """Handle application closing."""
        if self.bot_thread and self.bot_thread.is_running():
            self.bot_thread.stop_bot()
        
        self.root.destroy()
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = StumbleBotApp()
    app.run()