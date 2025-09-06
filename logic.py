import logging
from pathlib import Path
from models import FileNode, FolderNode
import database

logger = logging.getLogger(__name__)

def build_folder_structure_db(conn, folder_index, root_path, include_subfolders=True):
    """
    Scans a directory and inserts file information into the database.
    Returns a list of inaccessible paths.
    """
    path_obj = Path(root_path)
    logger.debug(f"Building structure for directory: {path_obj} into DB. Subfolders: {include_subfolders}")
    if not path_obj.is_dir():
        logger.warning(f"Path is not a directory, cannot build structure: {path_obj}")
        return [str(path_obj)]

    inaccessible_paths = []
    database.clear_folder_data(conn, folder_index)

    nodes_to_insert = []

    iterator = path_obj.rglob('*') if include_subfolders else path_obj.glob('*')

    for item in iterator:
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