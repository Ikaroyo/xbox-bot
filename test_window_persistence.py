"""
Test Script para verificar la persistencia de ventana

Este script crea una ventana simple para probar las funcionalidades
de recordar posición y centrado de diálogos.
"""

import customtkinter as ctk
from tkinter import messagebox
import json
import os


class TestWindow:
    """Ventana de prueba para testing."""
    
    SETTINGS_FILE = "test_window_settings.json"
    DEFAULT_GEOMETRY = "400x300+200+200"
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Test - Persistencia de Ventana")
        
        # Load geometry
        self._load_geometry()
        
        # Create UI
        self._create_ui()
        
        # Setup close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _load_geometry(self):
        """Load saved geometry."""
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    geometry = settings.get('geometry', self.DEFAULT_GEOMETRY)
            else:
                geometry = self.DEFAULT_GEOMETRY
            
            self.root.geometry(geometry)
            print(f"Loaded geometry: {geometry}")
            
        except Exception as e:
            print(f"Error loading geometry: {e}")
            self.root.geometry(self.DEFAULT_GEOMETRY)
    
    def _save_geometry(self):
        """Save current geometry."""
        try:
            geometry = self.root.geometry()
            settings = {'geometry': geometry}
            
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            
            print(f"Saved geometry: {geometry}")
            
        except Exception as e:
            print(f"Error saving geometry: {e}")
    
    def _create_ui(self):
        """Create the UI."""
        # Title
        title = ctk.CTkLabel(self.root, text="Test de Persistencia", 
                            font=("Arial", 16, "bold"))
        title.pack(pady=20)
        
        # Instructions
        instructions = ctk.CTkLabel(self.root, 
                                   text="1. Mueve y redimensiona esta ventana\n"
                                        "2. Cierra la aplicación\n"
                                        "3. Vuelve a abrirla\n"
                                        "4. Debería aparecer en la misma posición",
                                   justify="left")
        instructions.pack(pady=10)
        
        # Test centered dialog button
        test_btn = ctk.CTkButton(self.root, text="Test Diálogo Centrado", 
                                command=self._test_centered_dialog)
        test_btn.pack(pady=20)
        
        # Current geometry display
        self.geometry_label = ctk.CTkLabel(self.root, text="")
        self.geometry_label.pack(pady=10)
        
        # Update geometry display periodically
        self._update_geometry_display()
    
    def _update_geometry_display(self):
        """Update the geometry display."""
        try:
            geometry = self.root.geometry()
            self.geometry_label.configure(text=f"Geometría actual: {geometry}")
        except:
            pass
        
        # Schedule next update
        self.root.after(1000, self._update_geometry_display)
    
    def _test_centered_dialog(self):
        """Test centered dialog."""
        # Create a simple dialog to test centering
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Diálogo de Prueba")
        dialog.geometry("300x150")
        
        # Center it on the main window
        self._center_dialog(dialog)
        
        # Add content
        label = ctk.CTkLabel(dialog, text="Este diálogo debería estar\ncentrado sobre la ventana principal")
        label.pack(pady=20)
        
        close_btn = ctk.CTkButton(dialog, text="Cerrar", command=dialog.destroy)
        close_btn.pack(pady=10)
    
    def _center_dialog(self, dialog):
        """Center dialog on main window."""
        try:
            # Update main window to get accurate position/size
            self.root.update_idletasks()
            
            # Get main window position and size
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()
            
            # Update dialog to get its size
            dialog.update_idletasks()
            dialog_width = dialog.winfo_reqwidth()
            dialog_height = dialog.winfo_reqheight()
            
            # Calculate centered position
            center_x = main_x + (main_width - dialog_width) // 2
            center_y = main_y + (main_height - dialog_height) // 2
            
            # Set dialog position
            dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")
            
            print(f"Centered dialog at: {center_x}, {center_y}")
            
        except Exception as e:
            print(f"Error centering dialog: {e}")
    
    def _on_closing(self):
        """Handle window closing."""
        print("Saving geometry before closing...")
        self._save_geometry()
        self.root.destroy()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


if __name__ == "__main__":
    print("Iniciando test de persistencia de ventana...")
    app = TestWindow()
    app.run()
    print("Test completado.")