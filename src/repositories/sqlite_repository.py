from typing import List, Dict, Any, Optional
from interfaces.repository_interface import IFileRepository
from domain.file_info import FileInfo
import database

class SQLiteRepository(IFileRepository):
    """Encapsulates existing database operations within the repository interface."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def _get_connection(self):
        if not self._conn:
            self._conn = database.get_db_connection(self.db_path)
        return self._conn

    def get_all_files(self, folder_index: int, file_type_filter: str = "all") -> List[Dict[str, Any]]:
        rows = database.get_all_files(self._get_connection(), folder_index, file_type_filter)
        # We'll return dicts for now to maintain compatibility with legacy code
        columns = ['id', 'folder_index', 'path', 'name', 'ext', 'last_seen', 'size', 'modified_date', 'md5', 'llm_embedding']
        return [dict(zip(columns, row)) for row in rows]

    def get_files_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        rows = database.get_files_by_ids(self._get_connection(), ids)
        columns = ['id', 'folder_index', 'path', 'name', 'ext', 'last_seen', 'size', 'modified_date', 'md5', 'llm_embedding']
        return [dict(zip(columns, row)) for row in rows]

    def add_source(self, path: str) -> int:
        return database.add_source(self._get_connection(), path)

    def get_files_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        rows = database.get_files_by_ids(self._get_connection(), ids)
        columns = ['id', 'folder_index', 'path', 'name', 'ext', 'last_seen', 'size', 'modified_date', 'md5', 'llm_embedding']
        return [dict(zip(columns, row)) for row in rows]

    def add_source(self, path: str) -> int:
        return database.add_source(self._get_connection(), path)

    def get_sources(self) -> List[tuple]:
        return database.get_sources(self._get_connection())

    def delete_file_by_path(self, path: str, name: str):
        database.delete_file_by_path(self._get_connection(), path, name)

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
