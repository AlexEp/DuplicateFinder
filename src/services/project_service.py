import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from interfaces.repository_interface import IFileRepository
import database
import logic
from domain.comparison_options import ComparisonOptions

logger = logging.getLogger(__name__)

class ProjectService:
    """
    Service for managing projects and their data.
    
    This service acts as an abstraction layer between the controller and the
    repository for project-level operations such as saving settings,
    managing source folders, and syncing the filesystem with the database.
    """
    
    def __init__(self, repository: Optional[IFileRepository] = None):
        """Initializes the ProjectService with an optional repository."""
        self._repository = repository

    def set_repository(self, repository: IFileRepository):
        """Sets or updates the repository used by this service."""
        self._repository = repository

    def save_settings(self, options: ComparisonOptions):
        """Saves project settings to the repository."""
        if not self._repository:
            raise ValueError("Repository not initialized")
        
        conn = self._repository.connection
        if conn:
            database.save_setting(conn, 'project_settings', options.to_dict())
            logger.info("Project settings saved.")

    def load_settings(self) -> Optional[Dict[str, Any]]:
        """Loads project settings from the repository."""
        if not self._repository:
            return None
        
        conn = self._repository.connection
        if conn:
            return database.load_setting(conn, 'project_settings')
        return None

    def add_source(self, path: str) -> int:
        """Adds a source folder to the project."""
        if not self._repository:
            raise ValueError("Repository not initialized")
        return self._repository.add_source(path)

    def get_sources(self) -> List[tuple]:
        """Returns all source folders."""
        if not self._repository:
            return []
        return self._repository.get_sources()

    def sync_folders(self, folder_indices: List[int], include_subfolders: bool = True):
        """Syncs filesystem folders with the database."""
        if not self._repository:
            return []
        
        conn = self._repository.connection
        if not conn:
            return []
            
        sources = self.get_sources()
        source_map = {idx: path for idx, path in sources}
        
        inaccessible = []
        for idx in folder_indices:
            if idx in source_map:
                inaccessible.extend(logic.build_folder_structure_db(conn, idx, source_map[idx], include_subfolders))
        
        return inaccessible
