import hashlib
import logging
from pathlib import Path
import json
import database
from models import FileNode, FolderNode
from . import compare_by_histogram
from config import config
from .calculators import get_calculators, LLMEmbeddingCalculator

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
        
        if opts.get('compare_content_md5'):
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
    metadata only for the options specified using a modular calculator approach.
    Keys are relative paths to the provided base_path.
    Returns a tuple of (file_info, total_llm_files_processed).
    """
    logger.info(f"Flattening structure for base path '{base_path}' with options: {opts}")
    if opts is None: opts = {}
    
    file_info = {}
    base_path_obj = Path(base_path)
    image_extensions = config.get("file_extensions.image", [])
    
    # Initialize calculators
    calculators = get_calculators(llm_engine, progress_callback)
    llm_calculator = next((c for c in calculators if isinstance(c, LLMEmbeddingCalculator)), None)

    # --- Pre-computation for progress tracking ---
    files_to_process = []
    def collect_files(node):
        if isinstance(node, FileNode):
            files_to_process.append(node)
        elif isinstance(node, FolderNode):
            for child in node.content:
                collect_files(child)
    for root_node in structure:
        collect_files(root_node)

    if llm_calculator:
        llm_files_to_process = [ 
            node for node in files_to_process 
            if Path(node.fullpath).suffix.lower() in image_extensions
        ]
        llm_calculator.total_llm_files = len(llm_files_to_process)

    # --- Main Processing Loop ---
    for node in files_to_process:
        p = Path(node.fullpath)
        if not p.exists():
            logger.warning(f"File listed in structure does not exist, skipping: {p}")
            continue

        # File type filtering
        if file_type_filter != "all":
            ext = p.suffix.lower()
            allowed_extensions = config.get(f"file_extensions.{file_type_filter}", [])
            if ext not in allowed_extensions:
                continue

        try:
            relative_path = p.relative_to(base_path_obj)
        except ValueError:
            logger.warning(f"Could not determine relative path for {p} against base {base_path_obj}, skipping.")
            continue

        # Dynamically run calculators
        for calculator in calculators:
            calculator.calculate(node, opts)

        # Collect results
        info = node.metadata.copy()
        info['fullpath'] = node.fullpath
        if opts.get('compare_name'):
            info['name'] = node.name

        file_info[relative_path] = info

    total_llm_files = llm_calculator.processed_llm_files if llm_calculator else 0
    return file_info, total_llm_files