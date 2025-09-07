import logging
from pathlib import Path
from models import FileNode, FolderNode
import database

logger = logging.getLogger(__name__)

import time

def build_folder_structure_db(conn, folder_index, root_path, include_subfolders=True):
    """
    Scans a directory and syncs file information into the database using an UPSERT strategy.
    Removes files from the database that are no longer present in the filesystem.
    Returns a list of inaccessible paths.
    """
    path_obj = Path(root_path)
    logger.debug(f"Syncing structure for directory: {path_obj} into DB. Subfolders: {include_subfolders}")
    if not path_obj.is_dir():
        logger.warning(f"Path is not a directory, cannot build structure: {path_obj}")
        return [str(path_obj)]

    inaccessible_paths = []
    scan_start_time = time.time()

    nodes_to_sync = []
    iterator = path_obj.rglob('*') if include_subfolders else path_obj.glob('*')

    for item in iterator:
        try:
            if item.is_file():
                relative_path = item.relative_to(root_path).as_posix()
                nodes_to_sync.append({
                    'folder_index': folder_index,
                    'relative_path': relative_path,
                    'name': item.name,
                    'ext': item.suffix,
                    'size': item.stat().st_size,
                    'modified_date': item.stat().st_mtime,
                    'last_seen': scan_start_time
                })
        except OSError as e:
            logger.error(f"Cannot access item {item}: {e}")
            inaccessible_paths.append(str(item))

    with conn:
        if nodes_to_sync:
            conn.executemany("""
                INSERT INTO files (folder_index, relative_path, name, ext, size, modified_date, last_seen)
                VALUES (:folder_index, :relative_path, :name, :ext, :size, :modified_date, :last_seen)
                ON CONFLICT(folder_index, relative_path) DO UPDATE SET
                    name=excluded.name,
                    ext=excluded.ext,
                    size=excluded.size,
                    modified_date=excluded.modified_date,
                    last_seen=excluded.last_seen,
                    md5=CASE WHEN md5 IS NOT NULL THEN NULL ELSE md5 END,
                    histogram=CASE WHEN histogram IS NOT NULL THEN NULL ELSE histogram END,
                    llm_embedding=CASE WHEN llm_embedding IS NOT NULL THEN NULL ELSE llm_embedding END
            """, nodes_to_sync)

        # Remove files that were not seen in this scan
        delete_cursor = conn.execute(
            "DELETE FROM files WHERE folder_index = ? AND (last_seen < ? OR last_seen IS NULL)",
            (folder_index, scan_start_time)
        )
        logger.info(f"Removed {delete_cursor.rowcount} obsolete file entries for folder_index {folder_index}.")

    return inaccessible_paths

def build_folder_structure(root_path):
    """
    Recursively builds a tree of FileNode and FolderNode objects.
    Returns a tuple containing the content list and a list of inaccessible paths.
    """
    path_obj = Path(root_path)
    logger.debug(f"Building structure for directory: {path_obj}")
    if not path_obj.is_dir():
        logger.warning(f"Path is not a directory, cannot build structure: {path_obj}")
        return [], [str(path_obj)]

    content = []
    inaccessible_paths = []
    try:
        for item in sorted(path_obj.iterdir()):
            try:
                if item.is_dir():
                    folder_node = FolderNode(item)
                    folder_node.content, new_inaccessible = build_folder_structure(item)
                    content.append(folder_node)
                    inaccessible_paths.extend(new_inaccessible)
                elif item.is_file():
                    file_node = FileNode(item)
                    content.append(file_node)
            except OSError as e:
                logger.error(f"Cannot access item {item} in {path_obj}: {e}")
                inaccessible_paths.append(str(item))
    except OSError as e:
        logger.error(f"Cannot iterate directory {path_obj}: {e}")
        inaccessible_paths.append(str(path_obj))
    return content, inaccessible_paths