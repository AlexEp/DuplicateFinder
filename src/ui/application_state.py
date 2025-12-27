"""Application state management."""
from typing import Dict, List, Optional, Any
from domain.comparison_options import ComparisonOptions
from pathlib import Path


class ApplicationState:
    """Centralized application state."""
    
    def __init__(self):
        self._folder_structures: Dict[int, Any] = {}
        self._folder_paths: List[str] = []
        self._move_to_path: str = ""
        self._options = ComparisonOptions()
        self._current_project_path: Optional[Path] = None
    
    @property
    def folder_structures(self) -> Dict[int, Any]:
        return self._folder_structures
    
    @folder_structures.setter
    def folder_structures(self, value: Dict[int, Any]):
        self._folder_structures = value
    
    @property
    def folder_paths(self) -> List[str]:
        return self._folder_paths
    
    def add_folder_path(self, path: str):
        if path not in self._folder_paths:
            self._folder_paths.append(path)
    
    def remove_folder_path(self, path: str):
        if path in self._folder_paths:
            self._folder_paths.remove(path)
    
    def clear_folders(self):
        self._folder_paths.clear()
        self._folder_structures.clear()
    
    @property
    def options(self) -> ComparisonOptions:
        return self._options
    
    @options.setter
    def options(self, value: ComparisonOptions):
        self._options = value
    
    @property
    def move_to_path(self) -> str:
        return self._move_to_path
    
    @move_to_path.setter
    def move_to_path(self, value: str):
        self._move_to_path = value
    
    @property
    def current_project_path(self) -> Optional[Path]:
        return self._current_project_path
    
    @current_project_path.setter
    def current_project_path(self, value: Optional[Path]):
        self._current_project_path = value
