"""Status bar component."""
import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    """Encapsulates the status label and progress bar."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self._status_label = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self._status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self._progress.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def set_message(self, message: str):
        """Update the status message."""
        self._status_label.config(text=message)
        self.update_idletasks()
    
    def set_progress(self, value: float):
        """Update the progress bar value (0-100)."""
        self._progress['value'] = value
        self.update_idletasks()
    
    def clear_progress(self):
        """Reset the progress bar."""
        self._progress['value'] = 0
        self.update_idletasks()
