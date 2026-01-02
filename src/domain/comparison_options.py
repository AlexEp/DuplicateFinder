from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ComparisonOptions:
    """Value object for UI selections and settings."""
    file_type_filter: str = "all"
    include_subfolders: bool = True
    move_to_path: str = ""
    # Store all strategy-specific options in a dictionary
    options: Dict[str, Any] = field(default_factory=dict)

    DEFAULT_OPTIONS = {
        "compare_name": False,
        "compare_date": False,
        "compare_size": True,
        "compare_content_md5": False,
        "compare_histogram": False,
        "compare_llm": False,
        "histogram_method": "Correlation",
        "histogram_threshold": 0.9,
        "llm_similarity_threshold": 0.8
    }

    def __init__(self, file_type_filter="all", include_subfolders=True, move_to_path="", options=None, **kwargs):
        self.file_type_filter = file_type_filter
        self.include_subfolders = include_subfolders
        self.move_to_path = move_to_path
        
        # Start with defaults
        self.options = self.DEFAULT_OPTIONS.copy()
        
        # Apply dictionary if provided
        if options:
            self.options.update(options)
            
        # Apply any individual keyword arguments (legacy support)
        if kwargs:
            self.options.update(kwargs)

    def __getattr__(self, name: str) -> Any:
        # Fallback to options dictionary for backward compatibility
        if name in self.options:
            return self.options[name]
        # Check defaults just in case
        if name in self.DEFAULT_OPTIONS:
            return self.DEFAULT_OPTIONS[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def to_dict(self) -> Dict[str, Any]:
        """
        Provides a dictionary compatible with legacy components (flattened with 'options' key).
        """
        flat = {
            "file_type_filter": self.file_type_filter,
            "move_to_path": self.move_to_path,
            "include_subfolders": self.include_subfolders,
        }
        flat.update(self.options)
        # Nested 'options' part for find_duplicates_strategy.run logic
        flat["options"] = flat.copy()
        return flat

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Alias for to_dict for backward compatibility."""
        return self.to_dict()

    def to_save_dict(self) -> Dict[str, Any]:
        """Bridge method to return old-style nested options dictionary for database persistence."""
        opts = {
            "include_subfolders": self.include_subfolders,
        }
        opts.update(self.options)
        return {
            "file_type_filter": self.file_type_filter,
            "move_to_path": self.move_to_path,
            "options": opts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComparisonOptions':
        """Create from dictionary."""
        opts_data = data.get('options', {})
        
        # Extract core fields
        file_type_filter = data.get('file_type_filter', 'all')
        move_to_path = data.get('move_to_path', '')
        include_subfolders = opts_data.get('include_subfolders', True)
        
        # Strategy options (everything else in opts_data)
        strategy_opts = {k: v for k, v in opts_data.items() if k != 'include_subfolders'}
        
        return cls(
            file_type_filter=file_type_filter,
            move_to_path=move_to_path,
            include_subfolders=include_subfolders,
            options=strategy_opts
        )
