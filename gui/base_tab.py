"""
Base Tab Class

Provides common functionality for all tab components.
"""

import customtkinter as ctk
import tkinter as tk
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


class BaseTab(ABC):
    """Base class for all tab components."""
    
    def __init__(self, parent, app_instance):
        """
        Initialize the base tab.
        
        Args:
            parent: Parent widget (usually CTkTabview tab)
            app_instance: Reference to main application instance
        """
        self.parent = parent
        self.app = app_instance
        self.widgets = {}
        
        # Setup the tab content
        self.setup_tab()
    
    @abstractmethod
    def setup_tab(self):
        """Setup the tab content. Must be implemented by subclasses."""
        pass
    
    def add_log(self, message: str):
        """Add a log message via the main app."""
        if hasattr(self.app, '_add_log'):
            self.app._add_log(message)
        else:
            print(f"[{self.__class__.__name__}] {message}")
    
    def create_section_frame(self, title: str, parent_widget=None, pack_options: dict = None) -> ctk.CTkFrame:
        """
        Create a titled section frame.
        
        Args:
            title: Section title
            parent_widget: Parent widget (defaults to self.parent)
            pack_options: Additional pack options
            
        Returns:
            Created frame
        """
        if parent_widget is None:
            parent_widget = self.parent
        
        if pack_options is None:
            pack_options = {"fill": "x", "pady": (0, 10)}
        
        frame = ctk.CTkFrame(parent_widget)
        frame.pack(**pack_options)
        
        title_label = ctk.CTkLabel(frame, text=title, 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=(10, 5))
        
        return frame
    
    def create_labeled_entry(self, parent, label: str, placeholder: str = "", 
                           width: int = 120) -> tuple[ctk.CTkFrame, ctk.CTkEntry]:
        """
        Create a labeled entry widget.
        
        Args:
            parent: Parent widget
            label: Label text
            placeholder: Placeholder text
            width: Label width
            
        Returns:
            Tuple of (frame, entry)
        """
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=2)
        
        label_widget = ctk.CTkLabel(frame, text=label, width=width)
        label_widget.pack(side="left", padx=5)
        
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True, padx=5)
        
        return frame, entry
    
    def create_button_row(self, parent, buttons: list[tuple[str, Callable]], 
                         pack_options: dict = None) -> ctk.CTkFrame:
        """
        Create a row of buttons.
        
        Args:
            parent: Parent widget
            buttons: List of (text, callback) tuples
            pack_options: Pack options for the frame
            
        Returns:
            Button frame
        """
        if pack_options is None:
            pack_options = {"fill": "x", "padx": 10, "pady": 10}
        
        frame = ctk.CTkFrame(parent)
        frame.pack(**pack_options)
        
        for text, callback in buttons:
            btn = ctk.CTkButton(frame, text=text, command=callback, width=120)
            btn.pack(side="left", padx=5)
        
        return frame
    
    def show_error(self, message: str, title: str = "Error"):
        """Show error message dialog."""
        if hasattr(self.app, 'show_centered_messagebox'):
            self.app.show_centered_messagebox(title, message, "error")
        else:
            tk.messagebox.showerror(title, message)
    
    def show_info(self, message: str, title: str = "Information"):
        """Show info message dialog."""
        if hasattr(self.app, 'show_centered_messagebox'):
            self.app.show_centered_messagebox(title, message, "info")
        else:
            tk.messagebox.showinfo(title, message)
    
    def show_warning(self, message: str, title: str = "Warning"):
        """Show warning message dialog."""
        if hasattr(self.app, 'show_centered_messagebox'):
            self.app.show_centered_messagebox(title, message, "warning")
        else:
            tk.messagebox.showwarning(title, message)
    
    def ask_yes_no(self, message: str, title: str = "Confirm") -> bool:
        """Show yes/no dialog."""
        if hasattr(self.app, 'show_centered_messagebox'):
            return self.app.show_centered_messagebox(title, message, "question")
        else:
            return tk.messagebox.askyesno(title, message)
    
    def get_widget(self, name: str) -> Optional[Any]:
        """Get a stored widget by name."""
        return self.widgets.get(name)
    
    def store_widget(self, name: str, widget: Any):
        """Store a widget for later access."""
        self.widgets[name] = widget