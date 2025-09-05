import logging
from pathlib import Path
from models import FileNode
import database

logger = logging.getLogger(__name__)

def build_folder_structure_db(conn, folder_index, root_path):
    """
    Recursively scans a directory and inserts file information into the database.
    Returns a list of inaccessible paths.
    """
    path_obj = Path(root_path)
    logger.debug(f"Building structure for directory: {path_obj} into DB")
    if not path_obj.is_dir():
        logger.warning(f"Path is not a directory, cannot build structure: {path_obj}")
        return [str(path_obj)]

    inaccessible_paths = []
    database.clear_folder_data(conn, folder_index)

    nodes_to_insert = []

    for item in path_obj.rglob('*'):
        try:
            if item.is_file():
                relative_path = item.relative_to(root_path).as_posix()
                nodes_to_insert.append({
                    'folder_index': folder_index,
                    'relative_path': relative_path,
                    'name': item.name,
                    'ext': item.suffix,
                    'size': item.stat().st_size,
                    'modified_date': item.stat().st_mtime
                })
        except OSError as e:
            logger.error(f"Cannot access item {item}: {e}")
            inaccessible_paths.append(str(item))

    if nodes_to_insert:
        with conn:
            conn.executemany("""
                INSERT INTO files (folder_index, relative_path, name, ext, size, modified_date)
                VALUES (:folder_index, :relative_path, :name, :ext, :size, :modified_date)
            """, nodes_to_insert)

    return inaccessible_paths

def build_folder_structure(root_path):
    """
    Builds a flat list of FileNode objects from a directory.
    This is more efficient and aligns with the DB-based approach.
    """
    path_obj = Path(root_path)
    logger.debug(f"Building structure for directory: {path_obj}")
    if not path_obj.is_dir():
        logger.warning(f"Path is not a directory, cannot build structure: {path_obj}")
        return [], [str(path_obj)]

    content = []
    inaccessible_paths = []

    for item in path_obj.rglob('*'):
        try:
            if item.is_file():
                # Pass root_path to FileNode to store relative path correctly
                file_node = FileNode(item, root_path)
                content.append(file_node)
        except OSError as e:
            logger.error(f"Cannot access item {item}: {e}")
            inaccessible_paths.append(str(item))

    return content, inaccessible_paths