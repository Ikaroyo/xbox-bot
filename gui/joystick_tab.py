"""
Joystick Tab

Manual controller testing and sequence validation.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
from typing import Optional

from .base_tab import BaseTab
from modules.virtual_controller import XboxButton


class JoystickTab(BaseTab):
    """Joystick tab for manual controller testing."""
    
    def setup_tab(self):
        """Setup the Joystick tab content."""
        # Create main container
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup sections
        self._setup_manual_controls_section(main_frame)
        self._setup_sequence_tester_section(main_frame)
        self._setup_controller_status_section(main_frame)
    
    def _setup_manual_controls_section(self, parent):
        """Setup manual button controls section."""
        controls_frame = self.create_section_frame("Manual Controller", parent)
        
        # Controller grid layout
        grid_frame = ctk.CTkFrame(controls_frame)
        grid_frame.pack(pady=10)
        
        # Button layout (similar to Xbox controller)
        buttons_layout = [
            # Row 1: Triggers
            [("LEFT_TRIGGER", 0, 1), None, None, ("RIGHT_TRIGGER", 0, 5)],
            # Row 2: Bumpers  
            [("LEFT_BUMPER", 1, 1), None, None, ("RIGHT_BUMPER", 1, 5)],
            # Row 3: D-pad and face buttons
            [None, ("DPAD_UP", 2, 2), None, ("Y", 2, 4), None],
            [("DPAD_LEFT", 3, 1), ("DPAD_DOWN", 3, 2), ("DPAD_RIGHT", 3, 3), ("X", 3, 4), ("B", 3, 5)],
            [None, None, None, ("A", 4, 4), None],
            # Row 4: Special buttons
            [None, ("VIEW", 5, 1), ("GUIDE", 5, 2), ("MENU", 5, 3), None],
            # Row 5: Stick buttons
            [("LEFT_STICK", 6, 1), None, None, ("RIGHT_STICK", 6, 5)]
        ]
        
        self.controller_buttons = {}
        
        for row_idx, row in enumerate(buttons_layout):
            for item in row:
                if item:
                    button_name, grid_row, grid_col = item
                    btn = ctk.CTkButton(
                        grid_frame,
                        text=button_name.replace("_", "\n"),
                        width=80,
                        height=50,
                        command=lambda b=button_name: self._press_button(b)
                    )
                    btn.grid(row=grid_row, column=grid_col, padx=2, pady=2)
                    self.controller_buttons[button_name] = btn
        
        # Press duration setting
        duration_frame = ctk.CTkFrame(controls_frame)
        duration_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(duration_frame, text="Press Duration (s):", width=140).pack(side="left", padx=5)
        self.button_duration_entry = ctk.CTkEntry(duration_frame, width=80)
        self.button_duration_entry.pack(side="left", padx=5)
        self.button_duration_entry.insert(0, "0.1")
        self.store_widget("button_duration_entry", self.button_duration_entry)
        
        # Status label
        self.button_status_label = ctk.CTkLabel(controls_frame, text="Ready")
        self.button_status_label.pack(pady=5)
        self.store_widget("button_status_label", self.button_status_label)
    
    def _setup_sequence_tester_section(self, parent):
        """Setup sequence testing section."""
        sequence_frame = self.create_section_frame("Sequence Tester", parent)
        
        # Sequence input
        input_frame = ctk.CTkFrame(sequence_frame)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(input_frame, text="Sequence:", width=100).pack(side="left", padx=5)
        self.sequence_test_entry = ctk.CTkEntry(
            input_frame, 
            placeholder_text="DPAD_UP:2,DPAD_LEFT:1.5,DPAD_RIGHT:1"
        )
        self.sequence_test_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.store_widget("sequence_test_entry", self.sequence_test_entry)
        
        # Sequence buttons
        sequence_buttons = [
            ("Test Sequence", self._test_sequence),
            ("Stop Sequence", self._stop_sequence),
            ("Validate Syntax", self._validate_sequence)
        ]
        
        self.create_button_row(sequence_frame, sequence_buttons)
        
        # Sequence examples
        examples_frame = ctk.CTkFrame(sequence_frame)
        examples_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(examples_frame, text="Examples:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=2)
        
        examples = [
            "Simple: A:0.5,B:0.3,X:1.0",
            "Navigation: DPAD_UP:2,DPAD_LEFT:1.5,DPAD_RIGHT:1",
            "Combat: LEFT_BUMPER:0.2,A:0.1,RIGHT_TRIGGER:3",
            "Complex: Y:0.5,DPAD_DOWN:2,A:0.3,MENU:0.1"
        ]
        
        for example in examples:
            example_frame = ctk.CTkFrame(examples_frame)
            example_frame.pack(fill="x", padx=5, pady=1)
            
            ctk.CTkLabel(example_frame, text=example, font=("Consolas", 10)).pack(side="left", padx=5)
            copy_btn = ctk.CTkButton(
                example_frame, 
                text="Use", 
                width=50, 
                height=25,
                command=lambda seq=example.split(": ")[1]: self._use_example_sequence(seq)
            )
            copy_btn.pack(side="right", padx=5)
        
        # Sequence status
        self.sequence_status_label = ctk.CTkLabel(sequence_frame, text="Ready")
        self.sequence_status_label.pack(pady=5)
        self.store_widget("sequence_status_label", self.sequence_status_label)
        
        # Sequence progress
        self.sequence_progress = ctk.CTkProgressBar(sequence_frame)
        self.sequence_progress.pack(fill="x", padx=10, pady=5)
        self.sequence_progress.set(0)
        self.store_widget("sequence_progress", self.sequence_progress)
        
        # Control flags
        self.sequence_running = False
        self.sequence_stop_flag = False
    
    def _setup_controller_status_section(self, parent):
        """Setup controller connection status section."""
        status_frame = self.create_section_frame("Controller Status", parent)
        
        # Connection status
        connection_frame = ctk.CTkFrame(status_frame)
        connection_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(connection_frame, text="Status:", width=100).pack(side="left", padx=5)
        self.controller_status_label = ctk.CTkLabel(connection_frame, text="Checking...")
        self.controller_status_label.pack(side="left", padx=5)
        self.store_widget("controller_status_label", self.controller_status_label)
        
        # Test connection button
        test_connection_btn = ctk.CTkButton(
            status_frame,
            text="Test Controller Connection",
            command=self._test_controller_connection,
            width=200
        )
        test_connection_btn.pack(pady=5)
        
        # Controller info
        info_frame = ctk.CTkFrame(status_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = (
            "Virtual Xbox 360 Controller\n"
            "• Uses vgamepad library\n"
            "• Simulates real controller input\n"
            "• Works with most games and applications"
        )
        
        info_label = ctk.CTkLabel(info_frame, text=info_text, justify="left")
        info_label.pack(padx=10, pady=10)
        
        # Check status on startup
        self.app.root.after(1000, self._check_controller_status)
    
    def _press_button(self, button_name: str):
        """Press a single controller button."""
        try:
            duration = float(self.button_duration_entry.get())
            if duration <= 0:
                raise ValueError("Duration must be positive")
        except ValueError:
            self.show_error("Invalid duration value")
            return
        
        # Update status
        self.button_status_label.configure(text=f"Pressing {button_name}...")
        
        # Delegate to main app's controller
        if hasattr(self.app, 'virtual_controller'):
            threading.Thread(
                target=self._press_button_thread,
                args=(button_name, duration),
                daemon=True
            ).start()
        else:
            self.show_error("Virtual controller not available")
    
    def _press_button_thread(self, button_name: str, duration: float):
        """Thread function for pressing a button."""
        try:
            if hasattr(self.app, 'virtual_controller'):
                self.app.virtual_controller.press_button(XboxButton(button_name), duration)
            
            # Update status back to ready
            self.app.root.after(int(duration * 1000) + 100, 
                      lambda: self.button_status_label.configure(text="Ready"))
        except Exception as e:
            self.app.root.after(0, lambda: self.show_error(f"Button press failed: {str(e)}"))
    
    def _test_sequence(self):
        """Test a controller sequence."""
        if self.sequence_running:
            self.show_error("Sequence already running")
            return
        
        sequence = self.sequence_test_entry.get().strip()
        if not sequence:
            self.show_error("Please enter a sequence")
            return
        
        # Validate sequence first
        if not self._validate_sequence_syntax(sequence):
            return
        
        # Start sequence in thread
        self.sequence_running = True
        self.sequence_stop_flag = False
        
        threading.Thread(
            target=self._test_sequence_thread,
            args=(sequence,),
            daemon=True
        ).start()
    
    def _test_sequence_thread(self, sequence: str):
        """Thread function for testing sequence."""
        try:
            if not hasattr(self.app, 'virtual_controller'):
                self.app.root.after(0, lambda: self.show_error("Virtual controller not available"))
                return
            
            # Parse sequence
            steps = []
            for step in sequence.split(','):
                step = step.strip()
                if ':' in step:
                    button_name, duration_str = step.split(':', 1)
                    button_name = button_name.strip()
                    duration = float(duration_str.strip())
                    steps.append((button_name, duration))
            
            total_duration = sum(step[1] for step in steps)
            current_time = 0
            
            self.app.root.after(0, lambda: self.sequence_status_label.configure(text="Running sequence..."))
            
            for i, (button_name, duration) in enumerate(steps):
                if self.sequence_stop_flag:
                    break
                
                # Update status
                self.app.root.after(0, lambda b=button_name, d=duration: 
                          self.sequence_status_label.configure(text=f"Step {i+1}: {b} ({d}s)"))
                
                # Press button
                self.app.virtual_controller.press_button(XboxButton(button_name), duration)
                
                # Update progress
                current_time += duration
                progress = current_time / total_duration
                self.app.root.after(0, lambda p=progress: self.sequence_progress.set(p))
                
                # Small delay between steps
                time.sleep(0.1)
            
            # Complete
            self.app.root.after(0, self._sequence_complete)
            
        except Exception as e:
            self.app.root.after(0, lambda: self.show_error(f"Sequence failed: {str(e)}"))
            self.app.root.after(0, self._sequence_complete)
    
    def _stop_sequence(self):
        """Stop the running sequence."""
        if self.sequence_running:
            self.sequence_stop_flag = True
            self.sequence_status_label.configure(text="Stopping...")
    
    def _sequence_complete(self):
        """Called when sequence completes or stops."""
        self.sequence_running = False
        self.sequence_stop_flag = False
        self.sequence_progress.set(0)
        self.sequence_status_label.configure(text="Ready")
    
    def _validate_sequence(self):
        """Validate sequence syntax without running."""
        sequence = self.sequence_test_entry.get().strip()
        if not sequence:
            self.show_error("Please enter a sequence")
            return
        
        if self._validate_sequence_syntax(sequence):
            self.show_info("Sequence syntax is valid!", "Validation")
    
    def _validate_sequence_syntax(self, sequence: str) -> bool:
        """Validate sequence syntax."""
        try:
            valid_buttons = [button.value for button in XboxButton]
            
            for step in sequence.split(','):
                step = step.strip()
                if ':' not in step:
                    self.show_error(f"Invalid step format: {step}")
                    return False
                
                button_name, duration_str = step.split(':', 1)
                button_name = button_name.strip()
                
                if button_name not in valid_buttons:
                    self.show_error(f"Invalid button: {button_name}")
                    return False
                
                try:
                    duration = float(duration_str.strip())
                    if duration <= 0:
                        self.show_error(f"Invalid duration: {duration_str}")
                        return False
                except ValueError:
                    self.show_error(f"Invalid duration format: {duration_str}")
                    return False
            
            return True
            
        except Exception as e:
            self.show_error(f"Validation error: {str(e)}")
            return False
    
    def _use_example_sequence(self, sequence: str):
        """Use an example sequence."""
        self.sequence_test_entry.delete(0, 'end')
        self.sequence_test_entry.insert(0, sequence)
    
    def _test_controller_connection(self):
        """Test controller connection."""
        if hasattr(self.app, 'virtual_controller'):
            try:
                # Test with a very short button press
                self.app.virtual_controller.press_button(XboxButton.A, 0.01)
                self.controller_status_label.configure(text="✓ Connected", text_color="green")
                self.show_info("Controller connection successful!", "Connection Test")
            except Exception as e:
                self.controller_status_label.configure(text="✗ Error", text_color="red")
                self.show_error(f"Controller test failed: {str(e)}")
        else:
            self.controller_status_label.configure(text="✗ Not Available", text_color="red")
            self.show_error("Virtual controller not initialized")
    
    def _check_controller_status(self):
        """Check controller status on startup."""
        if hasattr(self.app, 'virtual_controller'):
            self.controller_status_label.configure(text="✓ Ready", text_color="green")
        else:
            self.controller_status_label.configure(text="✗ Not Available", text_color="red")