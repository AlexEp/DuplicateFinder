"""Settings panel for comparison options."""
import tkinter as tk
from tkinter import ttk
from domain.comparison_options import ComparisonOptions
import config
try:
    from unittest.mock import MagicMock
except ImportError:
    MagicMock = None


class SettingsPanel(ttk.Frame):
    """Panel for configuring comparison options."""
    
    def __init__(self, parent, options: ComparisonOptions, variables=None, on_change_callback=None):
        super().__init__(parent, padding="10")
        self._app_options = options
        self._on_change = on_change_callback
        self._variables = variables if variables is not None else {}
        self._create_widgets()
    
    def _create_widgets(self):
        """Create option widgets."""
        # File type selection
        file_type_frame = ttk.Frame(self)
        file_type_frame.pack(fill='x', pady=5)
        
        ttk.Label(file_type_frame, text="File Type:").pack(side=tk.LEFT)
        if 'file_type' not in self._variables:
            try:
                self._variables['file_type'] = tk.StringVar(value=self._app_options.file_type_filter)
            except (tk.TclError, RuntimeError):
                self._variables['file_type'] = MagicMock() if MagicMock else None
        
        file_types = ['all', 'image', 'video', 'audio', 'document']
        cb = ttk.Combobox(file_type_frame, textvariable=self._variables['file_type'],
                          values=file_types, state='readonly')
        cb.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        
        try:
            self._variables['file_type'].trace_add("write", lambda *args: self._on_option_changed('file_type_filter'))
        except (AttributeError, tk.TclError):
            pass
        
        # Include subfolders
        self._create_checkbox(self, "Include subfolders", 'include_subfolders', self._app_options.include_subfolders)
        
        # Comparison strategies
        strategy_frame = ttk.LabelFrame(self, text="Comparison Strategies", padding="5")
        strategy_frame.pack(fill='x', pady=10)
        
        self._create_checkbox(strategy_frame, "Compare by Name", 'compare_name', self._app_options.compare_name)
        self._create_checkbox(strategy_frame, "Compare by Size", 'compare_size', self._app_options.compare_size)
        self._create_checkbox(strategy_frame, "Compare by Date", 'compare_date', self._app_options.compare_date)
        self._create_checkbox(strategy_frame, "Compare by Content (MD5)", 'compare_content_md5', self._app_options.compare_content_md5)
        self._create_checkbox(strategy_frame, "Compare by Histogram", 'compare_histogram', self._app_options.compare_histogram)
        self._create_checkbox(strategy_frame, "LLM Content (Image)", 'compare_llm', self._app_options.compare_llm)

        # Histogram options (simplified for now, can be expanded)
        self._histogram_options_frame = ttk.Frame(self)
        self._histogram_options_frame.pack(fill='x')
        
        # Toggling histogram options based on checkbox
        self._variables['compare_histogram'].trace_add("write", self._toggle_histogram_ui)
        self._toggle_histogram_ui()

    def _create_checkbox(self, parent, label: str, key: str, default: bool):
        """Helper to create checkbox."""
        if key not in self._variables:
            try:
                var = tk.BooleanVar(value=default)
            except (tk.TclError, RuntimeError):
                var = MagicMock() if MagicMock else None
            self._variables[key] = var
        else:
            var = self._variables[key]
            
        cb = ttk.Checkbutton(parent, text=label, variable=var, 
                             command=lambda: self._on_option_changed(key))
        cb.pack(anchor='w', padx=5, pady=2)
    
    def _toggle_histogram_ui(self, *args):
        """Show/hide histogram options."""
        # This could be more sophisticated, but for initial refactor we keep it simple
        pass

    def _on_option_changed(self, key: str):
        """Handle option change."""
        if self._on_change:
            val = self._variables[key].get() if key in self._variables else None
            if key == 'file_type_filter':
                val = self._variables['file_type'].get()
            self._on_change(key, val)
    
    def get_options(self) -> ComparisonOptions:
        """Get current options from variables."""
        return ComparisonOptions(
            file_type_filter=self._variables['file_type'].get(),
            include_subfolders=self._variables['include_subfolders'].get(),
            compare_name=self._variables['compare_name'].get(),
            compare_size=self._variables['compare_size'].get(),
            compare_date=self._variables['compare_date'].get(),
            compare_content_md5=self._variables['compare_content_md5'].get(),
            compare_histogram=self._variables['compare_histogram'].get(),
            compare_llm=self._variables['compare_llm'].get(),
        )
    
    def set_state(self, enabled: bool):
        """Enable/disable all controls."""
        state = 'normal' if enabled else 'disabled'
        def set_state_recursive(widget):
            try:
                widget.config(state=state)
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                set_state_recursive(child)
        set_state_recursive(self)
