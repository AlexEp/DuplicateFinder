from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

class IRepository(ABC):
    """Base repository interface."""
    
    @abstractmethod
    def connect(self, connection_string: str):
        """Establish connection to data store."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection."""
        pass

class IFileRepository(ABC):
    """Interface for database/file operations."""
    
    @abstractmethod
    def get_all_files(self, folder_index: int, file_type_filter: str = "all") -> List[Dict[str, Any]]:
        """Retrieve all files for a folder."""
        pass

    @abstractmethod
    def get_files_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """Retrieve files by their IDs."""
        pass

    @abstractmethod
    def add_source(self, path: str) -> int:
        """Add a source folder and return its index."""
        pass

    @abstractmethod
    def get_sources(self) -> List[tuple]:
        """Get all source folder paths and their IDs."""
        pass

    @abstractmethod
    def delete_file_by_path(self, path: str, name: str):
        """Delete a file from the repository."""
        pass

    @abstractmethod
    def save_file_metadata_batch(self, metadata_list: List[Dict[str, Any]]):
        """Save metadata for multiple files in a batch."""
        pass

    @property
    @abstractmethod
    def connection(self):
        """The underlying database connection."""
        pass
