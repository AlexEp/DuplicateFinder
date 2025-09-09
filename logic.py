import logging
from pathlib import Path
from models import FileNode, FolderNode
import database
from strategies.strategy_registry import get_strategy
import itertools

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
                relative_dir = item.parent.relative_to(root_path).as_posix()
                # Ensure relative_dir is empty string if it's the root itself
                if relative_dir == '.':
                    relative_dir = ''
                nodes_to_sync.append({
                    'folder_index': folder_index,
                    'path': relative_dir,
                    'name': item.name,
                    'ext': item.suffix,
                    'size': item.stat().st_size,
                    'modified_date': item.stat().st_mtime,
                    'last_seen': scan_start_time,
                    'md5': None,
                    'histogram': None,
                    'llm_embedding': None
                })
        except OSError as e:
            logger.error(f"Cannot access item {item}: {e}")
            inaccessible_paths.append(str(item))

    with conn:
        for node_data in nodes_to_sync:
            # Check if file already exists
            cursor = conn.execute(
                "SELECT id FROM files WHERE folder_index = ? AND path = ? AND name = ?",
                (node_data['folder_index'], node_data['path'], node_data['name'])
            )
            existing_file = cursor.fetchone()

            if existing_file:
                file_id = existing_file[0]
                # Update existing file's last_seen and metadata
                conn.execute(
                    "UPDATE files SET name = ?, ext = ?, last_seen = ? WHERE id = ?",
                    (node_data['name'], node_data['ext'], node_data['last_seen'], file_id)
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO file_metadata (file_id, size, modified_date, md5, histogram, llm_embedding)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (file_id, node_data['size'], node_data['modified_date'],
                     node_data.get('md5'), node_data.get('histogram'), node_data.get('llm_embedding'))
                )
            else:
                # Insert new file
                cursor = conn.execute(
                    """
                    INSERT INTO files (folder_index, path, name, ext, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (node_data['folder_index'], node_data['path'], node_data['name'],
                     node_data['ext'], node_data['last_seen'])
                )
                file_id = cursor.lastrowid
                conn.execute(
                    """
                    INSERT INTO file_metadata (file_id, size, modified_date, md5, histogram, llm_embedding)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (file_id, node_data['size'], node_data['modified_date'],
                     node_data.get('md5'), node_data.get('histogram'), node_data.get('llm_embedding'))
                )

        # Remove files that were not seen in this scan
        delete_cursor = conn.execute(
            "DELETE FROM files WHERE folder_index = ? AND (last_seen < ? OR last_seen IS NULL)",
            (folder_index, scan_start_time)
        )
        logger.info(f"Removed {delete_cursor.rowcount} obsolete file entries for folder_index {folder_index}.")

    return inaccessible_paths

def run_comparison(info1, info2, opts):
    """
    Runs the comparison between two sets of file information based on the selected options.
    """
    matches = []

    for file1_info in info1:
        for file2_info in info2:
            is_match = True
            for option, value in opts.items():
                if value:
                    strategy = get_strategy(option)
                    if strategy and not strategy.compare(file1_info, file2_info, opts):
                        is_match = False
                        break
            if is_match:
                matches.append(file1_info)

    return matches

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