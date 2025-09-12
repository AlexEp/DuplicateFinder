import hashlib
import logging
from .calculator_registry import get_calculators
import database

logger = logging.getLogger(__name__)

def calculate_md5(file_path, block_size=65536):
    """Calculates the MD5 hash of a file."""
    md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                md5.update(block)
        return md5.hexdigest()
    except OSError as e:
        logger.error(f"Could not calculate MD5 for {file_path}: {e}")
        return None

def calculate_metadata_db(conn, folder_index, root_path, opts, file_type_filter="all", llm_engine=None):
    """
    Calculates and stores metadata for all files in a given folder.
    """
    logger.info(f"Calculating metadata for folder {folder_index} with opts: {opts}")
    calculators = get_calculators()
    files = database.get_all_files(conn, folder_index, file_type_filter=file_type_filter)

    file_infos = []

    for file_data in files:
        file_id, _, path, name, ext, _, size, modified_date, md5, llm_embedding = file_data

        file_info = {
            'id': file_id,
            'folder_index': folder_index,
            'relative_path': path,
            'name': name,
            'ext': ext,
            'size': size,
            'modified_date': modified_date,
            'md5': md5,
            'llm_embedding': llm_embedding
        }

        # This is a simplified representation of the FileNode.
        # In a real implementation, we would fetch the FileNode from the database.
        from models import FileNode
        from pathlib import Path
        file_node = FileNode(Path(f"{root_path}/{path}/{name}"))
        file_node.metadata = file_info

        # Load existing histogram if available
        if opts.get('compare_histogram'):
            from .histogram.database import HistogramDatabase
            hist_db = HistogramDatabase()
            method = opts.get('histogram_method')
            existing_histogram = hist_db.load(conn, file_id, method)
            if existing_histogram:
                file_info['histogram'] = existing_histogram

        for calculator in calculators:
            result = calculator.calculate(file_node, opts)
            if result is not None:
                key = calculator.db_key
                file_info[key] = result

                if key == 'histogram':
                    from .histogram.database import HistogramDatabase
                    hist_db = HistogramDatabase()
                    method = opts.get('histogram_method')
                    hist_db.save(conn, file_id, result, method)
                else:
                    # Save the metadata to the database.
                    # This is a simplified approach. A more robust implementation would
                    # use the database classes in each strategy folder.
                    with conn:
                        conn.execute(
                            f"UPDATE file_metadata SET {key} = ? WHERE file_id = ?",
                            (result, file_id)
                        )

        file_infos.append(file_info)

    return file_infos, [] # Return empty list for inaccessible paths for now.
