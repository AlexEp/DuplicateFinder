from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

class IFileService(ABC):
    """Interface for file system operations."""
    
    @abstractmethod
    def scan_folder(self, path: Path, include_subfolders: bool = True) -> List[Dict[str, Any]]:
        """Scans a folder and returns a list of file info dicts."""
        pass
    
    @abstractmethod
    def delete_file(self, path: Path) -> bool:
        """Deletes a file."""
        pass
    
    @abstractmethod
    def move_file(self, source: Path, destination: Path) -> bool:
        """Moves a file."""
        pass

    @abstractmethod
    def open_folder(self, path: Path) -> bool:
        """Opens the containing folder of a path."""
        pass

class IComparisonService(ABC):
    """Interface for comparison operations."""
    
    @abstractmethod
    def compare_folders(self, folder_indices: List[int], options: Any) -> List[List[Any]]:
        """Compares folders and returns groups of matches."""
        pass
    
    @abstractmethod
    def find_duplicates(self, folder_index: int, options: Any) -> List[List[Any]]:
        """Finds duplicates in a single folder."""
        pass
