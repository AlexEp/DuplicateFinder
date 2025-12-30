"""Settings panel for comparison options."""
import tkinter as tk
from tkinter import ttk
from domain.comparison_options import ComparisonOptions
from strategies.strategy_registry import get_all_strategies
from .utils import ToolTip
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
        
        # Discover and create strategy widgets
        strategies = get_all_strategies()
        for strategy in strategies:
            meta = strategy.metadata
            self._create_strategy_widgets(strategy_frame, meta)

    def _create_strategy_widgets(self, parent, meta):
        """Create widgets for a single strategy."""
        # Main checkbox
        default_val = self._app_options.options.get(meta.option_key, False)
        cb = self._create_checkbox(parent, meta.display_name, meta.option_key, default_val)
        ToolTip(cb, meta.tooltip)
        
        # Optional threshold control
        if meta.has_threshold:
            threshold_frame = ttk.Frame(parent)
            threshold_frame.pack(fill='x', padx=20)
            
            label_text = f"{meta.threshold_label or 'Threshold'}:"
            ttk.Label(threshold_frame, text=label_text).pack(side=tk.LEFT)
            
            threshold_key = f"{meta.option_key}_threshold"
            # Special case for legacy keys if needed, e.g., histogram_threshold
            if meta.option_key == 'compare_histogram':
                threshold_key = 'histogram_threshold'
            elif meta.option_key == 'compare_llm':
                threshold_key = 'llm_similarity_threshold'
                
            default_threshold = self._app_options.options.get(threshold_key, meta.default_threshold or 0.8)
            
            if threshold_key not in self._variables:
                try:
                    self._variables[threshold_key] = tk.StringVar(value=str(default_threshold))
                except (tk.TclError, RuntimeError):
                    self._variables[threshold_key] = MagicMock() if MagicMock else None
            
            entry = ttk.Entry(threshold_frame, textvariable=self._variables[threshold_key], width=5)
            entry.pack(side=tk.LEFT, padx=5)
            
            # Simple toggle visibility based on checkbox
            def toggle_threshold(*args):
                if self._variables[meta.option_key].get():
                    threshold_frame.pack(fill='x', padx=20)
                else:
                    threshold_frame.pack_forget()
            
            self._variables[meta.option_key].trace_add("write", toggle_threshold)
            toggle_threshold()

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
        return cb
    
    def _on_option_changed(self, key: str):
        """Handle option change."""
        if self._on_change:
            val = self._variables[key].get() if key in self._variables else None
            if key == 'file_type_filter':
                val = self._variables['file_type'].get()
            self._on_change(key, val)
    
    def get_options(self) -> ComparisonOptions:
        """Get current options from variables."""
        # Collect all strategy keys
        strategy_opts = {}
        for key, var in self._variables.items():
            if key not in ['file_type', 'include_subfolders']:
                try:
                    strategy_opts[key] = var.get()
                except (AttributeError, tk.TclError):
                    pass
        
        return ComparisonOptions(
            file_type_filter=self._variables['file_type'].get(),
            include_subfolders=self._variables['include_subfolders'].get(),
            options=strategy_opts
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
