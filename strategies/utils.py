import hashlib
import logging
from pathlib import Path
import json
import database
from models import FileNode, FolderNode
from . import compare_by_histogram
from config import config

logger = logging.getLogger(__name__)

def calculate_md5(file_path):
    """Calculates the MD5 hash of a file."""
    logger.debug(f"Calculating MD5 for: {file_path}")
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except IOError as e:
        logger.error(f"Could not calculate MD5 for {file_path}: {e}")
        return None

def calculate_metadata_db(conn, folder_index, base_path, opts=None, file_type_filter="all", llm_engine=None, progress_callback=None):
    logger.info(f"Calculating metadata for folder index {folder_index} with options: {opts}")
    if opts is None:
        opts = {}

    files_to_update = []
    base_path_obj = Path(base_path)
    image_extensions = config.get("file_extensions.image", [])

    cursor = conn.cursor()
    cursor.execute("SELECT id, relative_path, md5, histogram, llm_embedding FROM files WHERE folder_index = ?", (folder_index,))
    all_files = cursor.fetchall()

    files_for_llm = []
    if opts.get('compare_llm') and llm_engine:
        for file_id, relative_path, _, _, llm_embedding in all_files:
            if Path(relative_path).suffix.lower() in image_extensions and llm_embedding is None:
                files_for_llm.append((file_id, relative_path))

    processed_llm_files = 0
    total_llm_files = len(files_for_llm)

    for file_id, relative_path, md5, histogram, llm_embedding in all_files:
        p = base_path_obj / relative_path
        if not p.exists():
            logger.warning(f"File in DB does not exist, skipping: {p}")
            continue

        update_data = {'id': file_id}
        
        if opts.get('compare_content_md5') and md5 is None:
            update_data['md5'] = calculate_md5(p)

        if opts.get('compare_histogram') and histogram is None:
            hist = compare_by_histogram.get_histogram(str(p))
            if hist is not None:
                update_data['histogram'] = json.dumps(hist.tolist())

        if opts.get('compare_llm') and llm_engine and llm_embedding is None and Path(relative_path).suffix.lower() in image_extensions:
            processed_llm_files += 1
            if progress_callback:
                progress_message = f"LLM Processing ({processed_llm_files}/{total_llm_files}): {p.name}"
                progress_callback(progress_message, processed_llm_files)
            
            embedding = llm_engine.get_image_embedding(str(p))
            if embedding is not None:
                update_data['llm_embedding'] = embedding.tobytes()

        if len(update_data) > 1:
            files_to_update.append(update_data)

    if files_to_update:
        with conn:
            for data in files_to_update:
                set_clause = ", ".join([f"{key} = ?" for key in data if key != 'id'])
                values = [data[key] for key in data if key != 'id'] + [data['id']]
                conn.execute(f"UPDATE files SET {set_clause} WHERE id = ?", values)
        logger.info(f"Updated metadata for {len(files_to_update)} files in folder {folder_index}.")

    # Now, fetch the data again to return it
    file_info = {}
    cursor.execute("SELECT * FROM files WHERE folder_index = ?", (folder_index,))
    columns = [description[0] for description in cursor.description]
    for row in cursor.fetchall():
        file_data = dict(zip(columns, row))
        file_info[file_data['relative_path']] = file_data

    return file_info, total_llm_files

def flatten_structure(structure, base_path, opts=None, file_type_filter="all", llm_engine=None, progress_callback=None):
    """
    Flattens the object tree into a dictionary of file info, calculating
    metadata only for the options specified.
    Keys are relative paths to the provided base_path.
    Returns a tuple of (file_info, total_llm_files_processed).
    """
    logger.info(f"Flattening structure for base path '{base_path}' with options: {opts}")
    if opts is None:
        opts = {}
    file_info = {}
    base_path_obj = Path(base_path)

    # Get total number of files for progress reporting
    llm_files_to_process = []
    image_extensions = config.get("file_extensions.image", [])
    if opts.get('compare_llm') and llm_engine:
        def find_llm_files(node):
            if isinstance(node, FileNode):
                if Path(node.fullpath).suffix.lower() in image_extensions:
                    llm_files_to_process.append(node)
            elif isinstance(node, FolderNode):
                for child in node.content:
                    find_llm_files(child)
        for root_node in structure:
            find_llm_files(root_node)

    processed_llm_files = 0
    total_llm_files = len(llm_files_to_process)

    def traverse(node):
        nonlocal processed_llm_files
        if isinstance(node, FileNode):
            p = Path(node.fullpath)
            if not p.exists():
                logger.warning(f"File listed in structure does not exist, skipping: {p}")
                return

            # File type filtering
            if file_type_filter != "all":
                ext = p.suffix.lower()
                if file_type_filter == "image" and ext not in image_extensions:
                    return
                if file_type_filter == "video" and ext not in config.get("file_extensions.video", []):
                    return
                if file_type_filter == "audio" and ext not in config.get("file_extensions.audio", []):
                    return
                if file_type_filter == "document" and ext not in config.get("file_extensions.document", []):
                    return

            try:
                relative_path = p.relative_to(base_path_obj)
            except ValueError:
                logger.warning(f"Could not determine relative path for {p} against base {base_path_obj}, skipping.")
                return

            # Start with existing metadata
            info = node.metadata.copy()
            info['fullpath'] = node.fullpath
            
            if opts.get('compare_name'):
                info['name'] = node.name

            needs_stat = opts.get('compare_size') or opts.get('compare_date')
            if needs_stat:
                try:
                    stat = p.stat()
                    if opts.get('compare_size'):
                        info['size'] = stat.st_size
                    if opts.get('compare_date'):
                        info['date'] = stat.st_mtime
                except OSError as e:
                    logger.error(f"Could not get stat for file {p}: {e}")

            if opts.get('compare_content_md5'):
                if 'md5' not in info or info['md5'] is None:
                    info['md5'] = calculate_md5(p)
                else:
                    logger.debug(f"Using cached MD5 for: {p}")

            if opts.get('compare_histogram'):
                if 'histogram' not in info or info['histogram'] is None:
                    hist = compare_by_histogram.get_histogram(str(p))
                    if hist is not None:
                        info['histogram'] = hist
                else:
                    logger.debug(f"Using cached histogram for: {p}")
            
            if opts.get('compare_llm') and llm_engine and node in llm_files_to_process:
                if 'llm_embedding' not in info or info['llm_embedding'] is None:
                    processed_llm_files += 1
                    if progress_callback:
                        progress_message = f"LLM Processing ({processed_llm_files}/{total_llm_files}): {p.name}"
                        progress_callback(progress_message, processed_llm_files)

                    embedding = llm_engine.get_image_embedding(str(p))
                    if embedding is not None:
                        info['llm_embedding'] = embedding.tolist()
                else:
                    logger.debug(f"Using cached LLM embedding for: {p}")
                    processed_llm_files += 1
                    if progress_callback:
                        progress_callback(f"LLM Cached ({processed_llm_files}/{total_llm_files}): {p.name}", processed_llm_files)

            # Update the node's metadata in-place for saving
            node.metadata.update(info)
            
            file_info[relative_path] = info

        elif isinstance(node, FolderNode):
            for child in node.content:
                traverse(child)

    for root_node in structure:
        traverse(root_node)

    return file_info, total_llm_files