"""Results view component."""
import tkinter as tk
from tkinter import ttk


class ResultsView(ttk.Frame):
    """Component for displaying comparison results in a TreeView."""
    
    def __init__(self, parent, on_double_click=None, on_right_click=None):
        super().__init__(parent)
        self._on_double_click = on_double_click
        self._on_right_click = on_right_click
        self._create_widgets()
    
    def _create_widgets(self):
        """Create TreeView and scrollbars."""
        self._tree = ttk.Treeview(self, columns=("path", "size", "modified"), show="tree headings")
        self._tree.heading("#0", text="Folder/File")
        self._tree.heading("path", text="Full Path")
        self._tree.heading("size", text="Size")
        self._tree.heading("modified", text="Modified Date")
        
        self._tree.column("#0", width=250)
        self._tree.column("path", width=400)
        self._tree.column("size", width=100)
        self._tree.column("modified", width=150)
        
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.config(yscrollcommand=scrollbar.set)
        
        if self._on_double_click:
            self._tree.bind("<Double-1>", lambda e: self._on_double_click(self._tree.identify_row(e.y)))
        
        if self._on_right_click:
            self._tree.bind("<Button-3>", self._on_right_click)
            # For MacOS compatibility
            self._tree.bind("<Button-2>", self._on_right_click)
            self._tree.bind("<Control-1>", self._on_right_click)

    @property
    def tree(self):
        """Expose tree for direct manipulation if needed (temporary)."""
        return self._tree

    def clear(self):
        """Clear all items from the tree."""
        for item in self._tree.get_children():
            self._tree.delete(item)
    
    def display(self, results):
        """Display results (this logic will be refined as results structure is standardized)."""
        # For now, it might be easier to let the controller/coordinator 
        # call tree methods directly or pass a more structured data.
        pass
    
    def insert_group(self, text, values=None):
        """Insert a group header."""
        return self._tree.insert("", tk.END, text=text, values=values, open=True)
    
    def insert_item(self, parent, text, values=None, tags=None):
        """Insert a file item."""
        return self._tree.insert(parent, tk.END, text=text, values=values, tags=tags)
    
    def get_selection(self):
        """Get selected items."""
        return self._tree.selection()
    
    def get_item(self, item_id):
        """Get item details."""
        return self._tree.item(item_id)
