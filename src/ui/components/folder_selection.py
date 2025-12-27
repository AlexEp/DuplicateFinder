"""Folder selection component."""
import tkinter as tk
from tkinter import ttk, filedialog


class FolderSelection(ttk.LabelFrame):
    """Component for managing the list of source folders."""
    
    def __init__(self, parent, on_change_callback=None):
        super().__init__(parent, text="Source Folders", padding="10")
        self._on_change = on_change_callback
        self._create_widgets()
    
    def _create_widgets(self):
        """Create listbox and buttons."""
        self._listbox = tk.Listbox(self, selectmode=tk.SINGLE, height=5)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.RIGHT, padx=5)

        self._add_btn = ttk.Button(button_frame, text="+", width=3, command=self._add_folder)
        self._add_btn.pack(pady=2)
        # ToolTip would be nice but it's defined in ui.py, 
        # for now we skip or move ToolTip to a shared or utils module

        self._remove_btn = ttk.Button(button_frame, text="-", width=3, command=self._remove_folder)
        self._remove_btn.pack(pady=2)
    
    def _add_folder(self):
        """Pick a folder and add to the list."""
        folder = filedialog.askdirectory()
        if folder:
            if folder not in self._listbox.get(0, tk.END):
                self._listbox.insert(tk.END, folder)
                if self._on_change:
                    self._on_change()
    
    def _remove_folder(self):
        """Remove selected folder."""
        selection = self._listbox.curselection()
        if selection:
            self._listbox.delete(selection)
            if self._on_change:
                self._on_change()
    
    def get_paths(self) -> list:
        """Get all folder paths in the list."""
        return list(self._listbox.get(0, tk.END))
    
    def set_paths(self, paths: list):
        """Set the list of folder paths."""
        self._listbox.delete(0, tk.END)
        for path in paths:
            self._listbox.insert(tk.END, path)
    
    def set_state(self, enabled: bool):
        """Enable/disable buttons."""
        state = 'normal' if enabled else 'disabled'
        self._add_btn.config(state=state)
        self._remove_btn.config(state=state)
        self._listbox.config(state=state)
