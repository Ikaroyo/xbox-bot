"""
Run Tab

Contains bot control and logging functionality.
"""

import customtkinter as ctk
import threading
from .base_tab import BaseTab


class RunTab(BaseTab):
    """Run tab with bot control and logging."""
    
    def setup_tab(self):
        """Setup the Run tab content."""
        self._setup_control_section()
        self._setup_log_section()
    
    def _setup_control_section(self):
        """Setup bot control section."""
        control_frame = ctk.CTkFrame(self.parent)
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
        self.store_widget("start_stop_btn", self.start_stop_btn)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Bot Status: Stopped",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=20, pady=10)
        self.store_widget("status_label", self.status_label)
        
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
        
        # Debug mode button
        self.debug_mode_btn = ctk.CTkButton(
            control_frame,
            text="Debug Mode",
            command=self._toggle_debug_mode,
            width=100
        )
        self.debug_mode_btn.pack(side="right", padx=(5, 10), pady=10)
        self.store_widget("debug_mode_btn", self.debug_mode_btn)
        
        self.debug_mode_enabled = False
    
    def _setup_log_section(self):
        """Setup logging section."""
        # Log label
        log_label = ctk.CTkLabel(self.parent, text="Bot Logs:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        log_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Log text area with scrollbar
        self.log_text = ctk.CTkTextbox(
            self.parent,
            width=750,
            height=400,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.store_widget("log_text", self.log_text)
        
        # Initial log message
        self.add_log("Application initialized. Ready to start bot.")
    
    def _toggle_bot(self):
        """Toggle bot start/stop state."""
        if hasattr(self.app, '_toggle_bot'):
            self.app._toggle_bot()
    
    def _show_debug_info(self):
        """Show debug information."""
        if hasattr(self.app, '_show_debug_info'):
            self.app._show_debug_info()
    
    def _clear_logs(self):
        """Clear the log text area."""
        if self.log_text:
            self.log_text.delete("1.0", "end")
    
    def _show_help(self):
        """Show help information."""
        if hasattr(self.app, '_show_help'):
            self.app._show_help()
    
    def _toggle_debug_mode(self):
        """Toggle debug mode."""
        if hasattr(self.app, '_toggle_debug_mode'):
            self.app._toggle_debug_mode()
    
    def update_bot_status(self, is_running: bool):
        """Update bot status display."""
        if is_running:
            self.start_stop_btn.configure(text="Stop Bot")
            self.status_label.configure(text="Bot Status: Running")
        else:
            self.start_stop_btn.configure(text="Start Bot")
            self.status_label.configure(text="Bot Status: Stopped")
    
    def update_debug_mode(self, enabled: bool):
        """Update debug mode display."""
        self.debug_mode_enabled = enabled
        if enabled:
            self.debug_mode_btn.configure(text="Debug ON", fg_color="orange")
        else:
            self.debug_mode_btn.configure(text="Debug Mode", fg_color=None)
    
    def add_log_message(self, message: str):
        """Add a message to the log display."""
        if self.log_text:
            self.log_text.insert("end", message + "\\n")
            self.log_text.see("end")