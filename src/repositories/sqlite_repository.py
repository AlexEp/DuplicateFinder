from typing import List, Dict, Any, Optional
from interfaces.repository_interface import IFileRepository
from domain.file_info import FileInfo
import database
import logging

logger = logging.getLogger(__name__)

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
        columns = ['id', 'folder_index', 'path', 'name', 'ext', 'last_seen', 'size', 'modified_date', 'md5', 'llm_embedding']
        return [dict(zip(columns, row)) for row in rows]

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

    def save_file_metadata_batch(self, metadata_list: List[Dict[str, Any]]):
        """Save metadata for multiple files in one transaction."""
        conn = self._get_connection()
        try:
            with conn:
                for meta in metadata_list:
                    file_id = meta.get('file_id')
                    if file_id is None:
                        continue
                    
                    # Implementation of UPSERT for file_metadata
                    # Check if exists
                    cursor = conn.execute("SELECT id FROM file_metadata WHERE file_id = ?", (file_id,))
                    if cursor.fetchone():
                        conn.execute("""
                            UPDATE file_metadata 
                            SET size = ?, modified_date = ?, md5 = ?, llm_embedding = ?
                            WHERE file_id = ?
                        """, (meta.get('size'), meta.get('modified_date'), meta.get('md5'), meta.get('llm_embedding'), file_id))
                    else:
                        conn.execute("""
                            INSERT INTO file_metadata (file_id, size, modified_date, md5, llm_embedding)
                            VALUES (?, ?, ?, ?, ?)
                        """, (file_id, meta.get('size'), meta.get('modified_date'), meta.get('md5'), meta.get('llm_embedding')))
        except Exception as e:
            logger.error(f"Error saving metadata batch: {e}")
            raise

    @property
    def connection(self):
        return self._get_connection()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
