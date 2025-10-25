"""
Configuration Tab

Contains rules management, template configuration, and bot settings.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
from typing import Optional

from .base_tab import BaseTab
from modules.virtual_controller import XboxButton


class ConfigurationTab(BaseTab):
    """Configuration tab with rules and settings management."""
    
    def setup_tab(self):
        """Setup the Configuration tab content."""
        # Create scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent, width=750, height=550)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initialize state variables
        self.current_rules = []
        self.selected_rule_index = None
        
        # Setup sections
        self._setup_window_config_section()
        self._setup_detection_rules_section()
        self._setup_bot_settings_section()
        self._setup_config_management_section()
    
    def _setup_window_config_section(self):
        """Setup window configuration section."""
        window_frame = self.create_section_frame("Window Configuration")
        
        # Window title
        _, self.window_title_entry = self.create_labeled_entry(
            window_frame, "Window Title:", "Xbox"
        )
        self.store_widget("window_title_entry", self.window_title_entry)
        
        # Window size
        size_frame = ctk.CTkFrame(window_frame)
        size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(size_frame, text="Target Size:", width=120).pack(side="left", padx=5)
        
        self.window_width_entry = ctk.CTkEntry(size_frame, placeholder_text="1280", width=100)
        self.window_width_entry.pack(side="left", padx=5)
        self.store_widget("window_width_entry", self.window_width_entry)
        
        ctk.CTkLabel(size_frame, text="x").pack(side="left", padx=2)
        
        self.window_height_entry = ctk.CTkEntry(size_frame, placeholder_text="720", width=100)
        self.window_height_entry.pack(side="left", padx=5)
        self.store_widget("window_height_entry", self.window_height_entry)
        
        # Test window button
        test_window_btn = ctk.CTkButton(
            window_frame,
            text="Test Window Detection",
            command=self._test_window_detection,
            width=200
        )
        test_window_btn.pack(pady=10)
    
    def _setup_detection_rules_section(self):
        """Setup detection rules management section."""
        rules_frame = self.create_section_frame("Detection Rules")
        
        # Rules list and controls
        rules_control_frame = ctk.CTkFrame(rules_frame)
        rules_control_frame.pack(fill="x", padx=10, pady=5)
        
        # Rules listbox
        self.rules_listbox = tk.Listbox(rules_control_frame, height=6, font=("Consolas", 10))
        self.rules_listbox.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.rules_listbox.bind('<<ListboxSelect>>', self._on_rule_select)
        self.store_widget("rules_listbox", self.rules_listbox)
        
        # Rules buttons
        rules_btn_frame = ctk.CTkFrame(rules_control_frame)
        rules_btn_frame.pack(side="right", fill="y")
        
        rule_buttons = [
            ("Add Rule", self._add_rule),
            ("Edit Rule", self._edit_rule),
            ("Delete Rule", self._delete_rule),
            ("Capture Template", self._capture_template)
        ]
        
        for text, command in rule_buttons:
            btn = ctk.CTkButton(rules_btn_frame, text=text, command=command, width=100)
            btn.pack(pady=2)
        
        # Rule details
        self._setup_rule_details_section(rules_frame)
    
    def _setup_rule_details_section(self, parent):
        """Setup rule details entry section."""
        details_frame = ctk.CTkFrame(parent)
        details_frame.pack(fill="x", padx=10, pady=5)
        
        # Rule name
        _, self.rule_name_entry = self.create_labeled_entry(
            details_frame, "Rule Name:", "MainMenu"
        )
        self.store_widget("rule_name_entry", self.rule_name_entry)
        
        # Template name with browse and preview
        template_frame = ctk.CTkFrame(details_frame)
        template_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(template_frame, text="Template:", width=120).pack(side="left", padx=5)
        self.template_name_entry = ctk.CTkEntry(template_frame, placeholder_text="main_menu.png")
        self.template_name_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.store_widget("template_name_entry", self.template_name_entry)
        
        # Template buttons
        template_btn_frame = ctk.CTkFrame(template_frame)
        template_btn_frame.pack(side="right", padx=5)
        
        ctk.CTkButton(template_btn_frame, text="Browse", command=self._browse_templates, width=70).pack(side="left", padx=2)
        ctk.CTkButton(template_btn_frame, text="Preview", command=self._preview_template, width=70).pack(side="left", padx=2)
        
        # Confidence slider
        conf_frame = ctk.CTkFrame(details_frame)
        conf_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(conf_frame, text="Confidence:", width=120).pack(side="left", padx=5)
        self.confidence_slider = ctk.CTkSlider(conf_frame, from_=0.5, to=1.0, number_of_steps=50)
        self.confidence_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.confidence_slider.set(0.8)
        self.store_widget("confidence_slider", self.confidence_slider)
        
        self.confidence_label = ctk.CTkLabel(conf_frame, text="0.80", width=50)
        self.confidence_label.pack(side="left", padx=5)
        self.store_widget("confidence_label", self.confidence_label)
        
        self.confidence_slider.configure(command=self._update_confidence_label)
        
        # Action type selection
        self._setup_action_section(details_frame)
        
        # Save rule button
        save_rule_btn = ctk.CTkButton(
            details_frame,
            text="Save Rule",
            command=self._save_rule,
            width=120
        )
        save_rule_btn.pack(pady=10)
    
    def _setup_action_section(self, parent):
        """Setup action configuration section."""
        # Action type selector
        action_frame = ctk.CTkFrame(parent)
        action_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(action_frame, text="Action:", width=120).pack(side="left", padx=5)
        
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
        
        # Simple action frame
        self.simple_action_frame = ctk.CTkFrame(parent)
        self.simple_action_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(self.simple_action_frame, text="Button:", width=120).pack(side="left", padx=5)
        
        available_actions = [button.value for button in XboxButton]
        self.action_combobox = ctk.CTkComboBox(self.simple_action_frame, values=available_actions)
        self.action_combobox.pack(side="left", fill="x", expand=True, padx=5)
        self.action_combobox.set("A")
        self.store_widget("action_combobox", self.action_combobox)
        
        # Sequence action frame
        self.sequence_action_frame = ctk.CTkFrame(parent)
        
        ctk.CTkLabel(self.sequence_action_frame, text="Sequence:", width=120).pack(side="left", padx=5)
        self.sequence_entry = ctk.CTkEntry(self.sequence_action_frame, 
                                          placeholder_text="DPAD_UP:2,DPAD_LEFT:1.5,DPAD_RIGHT:1")
        self.sequence_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.store_widget("sequence_entry", self.sequence_entry)
        
        # Sequence help button
        sequence_help_btn = ctk.CTkButton(self.sequence_action_frame, text="?", 
                                         command=self._show_sequence_help, width=30)
        sequence_help_btn.pack(side="right", padx=5)
        
        self.store_widget("simple_action_frame", self.simple_action_frame)
        self.store_widget("sequence_action_frame", self.sequence_action_frame)
    
    def _setup_bot_settings_section(self):
        """Setup bot timing and behavior settings."""
        settings_frame = self.create_section_frame("Bot Settings")
        
        # Loop delay
        _, self.loop_delay_entry = self.create_labeled_entry(
            settings_frame, "Loop Delay (s):", "0.1"
        )
        self.store_widget("loop_delay_entry", self.loop_delay_entry)
        
        # Action cooldown
        _, self.action_cooldown_entry = self.create_labeled_entry(
            settings_frame, "Action Cooldown (s):", "1.0"
        )
        self.store_widget("action_cooldown_entry", self.action_cooldown_entry)
        
        # Capture area size
        capture_frame = ctk.CTkFrame(settings_frame)
        capture_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(capture_frame, text="Capture Area:", width=120).pack(side="left", padx=5)
        
        self.capture_width_entry = ctk.CTkEntry(capture_frame, placeholder_text="100", width=80)
        self.capture_width_entry.pack(side="left", padx=5)
        self.store_widget("capture_width_entry", self.capture_width_entry)
        
        ctk.CTkLabel(capture_frame, text="x").pack(side="left", padx=2)
        
        self.capture_height_entry = ctk.CTkEntry(capture_frame, placeholder_text="100", width=80)
        self.capture_height_entry.pack(side="left", padx=5)
        self.store_widget("capture_height_entry", self.capture_height_entry)
    
    def _setup_config_management_section(self):
        """Setup configuration save/load section."""
        mgmt_frame = self.create_section_frame("Configuration Management")
        
        # Config buttons
        config_buttons = [
            ("Save Config", self._save_config),
            ("Load Config", self._load_config),
            ("Export Config", self._export_config),
            ("Import Config", self._import_config)
        ]
        
        self.create_button_row(mgmt_frame, config_buttons)
    
    # Event handlers - these will delegate to the main app
    def _test_window_detection(self):
        if hasattr(self.app, '_test_window_detection'):
            self.app._test_window_detection()
    
    def _on_rule_select(self, event):
        if hasattr(self.app, '_on_rule_select'):
            self.app._on_rule_select(event)
    
    def _add_rule(self):
        if hasattr(self.app, '_add_rule'):
            self.app._add_rule()
    
    def _edit_rule(self):
        if hasattr(self.app, '_edit_rule'):
            self.app._edit_rule()
    
    def _delete_rule(self):
        if hasattr(self.app, '_delete_rule'):
            self.app._delete_rule()
    
    def _capture_template(self):
        if hasattr(self.app, '_capture_template'):
            self.app._capture_template()
    
    def _browse_templates(self):
        if hasattr(self.app, '_browse_templates'):
            self.app._browse_templates()
    
    def _preview_template(self):
        if hasattr(self.app, '_preview_template'):
            self.app._preview_template()
    
    def _update_confidence_label(self, value):
        self.confidence_label.configure(text=f"{value:.2f}")
    
    def _on_action_type_change(self):
        action_type = self.action_type_var.get()
        
        if action_type == "simple":
            self.simple_action_frame.pack(fill="x", padx=5, pady=2)
            self.sequence_action_frame.pack_forget()
        else:  # sequence
            self.simple_action_frame.pack_forget()
            self.sequence_action_frame.pack(fill="x", padx=5, pady=2)
    
    def _show_sequence_help(self):
        if hasattr(self.app, '_show_sequence_help'):
            self.app._show_sequence_help()
    
    def _save_rule(self):
        if hasattr(self.app, '_save_rule'):
            self.app._save_rule()
    
    def _save_config(self):
        if hasattr(self.app, '_save_config'):
            self.app._save_config()
    
    def _load_config(self):
        if hasattr(self.app, '_load_config'):
            self.app._load_config()
    
    def _export_config(self):
        if hasattr(self.app, '_export_config'):
            self.app._export_config()
    
    def _import_config(self):
        if hasattr(self.app, '_import_config'):
            self.app._import_config()
    
    # Public methods for updating the UI
    def refresh_rules_list(self):
        """Refresh the rules listbox."""
        if hasattr(self.app, '_refresh_rules_list'):
            self.app._refresh_rules_list()
    
    def load_rule_to_details(self, index: int):
        """Load rule data to detail entries."""
        if hasattr(self.app, '_load_rule_to_details'):
            self.app._load_rule_to_details(index)