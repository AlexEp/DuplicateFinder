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
            if item.is_file() and not item.name.endswith('.cfp-db'):
                relative_dir = item.parent.relative_to(root_path).as_posix()
                # Ensure relative_dir is empty string if it's the root itself
                if relative_dir == '.':
                    relative_dir = ''
                nodes_to_sync.append({
                    'folder_index': folder_index,
                    'path': relative_dir,
                    'name': item.name,
                    'ext': item.suffix.lower(),
                    'size': item.stat().st_size,
                    'modified_date': item.stat().st_mtime,
                    'last_seen': scan_start_time,
                    'md5': None,
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
                # Get current metadata to check if it changed
                meta_cursor = conn.execute(
                    "SELECT size, modified_date FROM file_metadata WHERE file_id = ?",
                    (file_id,)
                )
                meta = meta_cursor.fetchone()
                
                # Update existing file's last_seen
                conn.execute(
                    "UPDATE files SET last_seen = ? WHERE id = ?",
                    (node_data['last_seen'], file_id)
                )
                
                if not meta or meta[0] != node_data['size'] or meta[1] != node_data['modified_date']:
                    # File has changed, reset expensive metadata
                    database.clear_file_metadata(conn, file_id)
                    conn.execute(
                        """
                        INSERT INTO file_metadata (file_id, size, modified_date, md5, llm_embedding, hash_fast, hash_accurate)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (file_id, node_data['size'], node_data['modified_date'], None, None, None, None)
                    )
                    logger.debug(f"File changed: {node_data['name']}. Metadata reset.")
                else:
                    # File hasn't changed, just update last_seen (already done)
                    pass
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
                    INSERT INTO file_metadata (file_id, size, modified_date, md5, llm_embedding, hash_fast, hash_accurate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (file_id, node_data['size'], node_data['modified_date'],
                     node_data.get('md5'), node_data.get('llm_embedding'),
                     node_data.get('hash_fast'), node_data.get('hash_accurate'))
                )

        # Remove files that were not seen in this scan
        # First, clean up all metadata for these files
        stale_files_query = "SELECT id FROM files WHERE folder_index = ? AND (last_seen < ? OR last_seen IS NULL)"
        stale_params = (folder_index, scan_start_time)
        
        conn.execute(f"DELETE FROM file_metadata WHERE file_id IN ({stale_files_query})", stale_params)
        conn.execute(f"DELETE FROM histogram_intersection WHERE file_id IN ({stale_files_query})", stale_params)
        conn.execute(f"DELETE FROM histogram_correlation WHERE file_id IN ({stale_files_query})", stale_params)
        conn.execute(f"DELETE FROM histogram_chisqr WHERE file_id IN ({stale_files_query})", stale_params)
        conn.execute(f"DELETE FROM histogram_bhattacharyya WHERE file_id IN ({stale_files_query})", stale_params)

        delete_cursor = conn.execute(
            "DELETE FROM files WHERE folder_index = ? AND (last_seen < ? OR last_seen IS NULL)",
            stale_params
        )
        logger.info(f"Removed {delete_cursor.rowcount} obsolete file entries and their metadata for folder_index {folder_index}.")

    return inaccessible_paths

def run_comparison(info1, info2, opts):
    """
    Finds common files between two lists of file information.
    First groups by exact match strategies, then refines groups using similarity strategies.
    Returns a list of groups, where each group contains matching files from both lists.
    """
    selected_strategies = []
    # Gather selected strategies from options
    for option, value in opts.get('options', {}).items():
        if value and option.startswith('compare_'):
            strategy = get_strategy(option)
            if strategy:
                selected_strategies.append(strategy)

    if not selected_strategies:
        return []

    exact_strategies = [s for s in selected_strategies if not getattr(s, 'is_similarity_strategy', False)]
    sim_strategies = [s for s in selected_strategies if getattr(s, 'is_similarity_strategy', False)]

    # If we have exact strategies, group by them. Otherwise, treat everything as one giant group.
    all_files_map = {}
    if exact_strategies:
        def get_exact_key(file_info):
            key = tuple(file_info.get(s.db_key) for s in exact_strategies)
            return None if any(k is None for k in key) else key

        for file_info in info1 + info2:
            key = get_exact_key(file_info)
            if key is not None:
                all_files_map.setdefault(key, []).append(file_info)
    else:
        # If there are only similarity strategies, all valid files go in one group
        valid_files = [f for f in info1 + info2 if all(f.get(s.db_key) is not None for s in sim_strategies)]
        if valid_files:
            all_files_map["all_files"] = valid_files

    matches = []
    for key, group in all_files_map.items():
        if len(group) > 1:
            # Check if the group contains files from at least two different sources
            # We will do this check AFTER similarity refinement if needed, 
            # but wait, it's more efficient to check now, wait! Similarity can split the group.
            # So refinement first.
            refined_groups = [group]
            
            for strategy in sim_strategies:
                next_refined_groups = []
                for rg in refined_groups:
                    while len(rg) > 1:
                        file1 = rg.pop(0)
                        matched = [file1]
                        unmatched = []
                        for file2 in rg:
                            if strategy.compare(file1, file2, opts):
                                matched.append(file2)
                            else:
                                unmatched.append(file2)
                        rg = unmatched
                        if len(matched) > 1:
                            next_refined_groups.append(matched)
                refined_groups = next_refined_groups

            # Now check that each refined group contains files from >= 2 different sources
            for rg in refined_groups:
                if len(rg) > 1:
                    folder_indices = {info.get('folder_index') for info in rg}
                    if len(folder_indices) > 1:
                        file_ids = {info.get('id') for info in rg}
                        if len(file_ids) > 1:
                            matches.append(rg)
            
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