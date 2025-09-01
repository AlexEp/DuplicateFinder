import hashlib
import logging
from pathlib import Path
import json
from models import FileNode, FolderNode
from . import compare_by_histogram

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

def load_image_extensions():
    """Loads the list of image extensions from settings.json."""
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
            extensions = settings.get("image_extensions")
            if isinstance(extensions, list):
                return [ext.lower() for ext in extensions]
    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load image extensions from settings.json: {e}")
    
    # Default extensions if settings are not available
    return ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.avif']

IMAGE_EXTENSIONS = load_image_extensions()
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.odt', '.rtf']

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
    if opts.get('compare_llm') and llm_engine:
        def find_llm_files(node):
            if isinstance(node, FileNode):
                if Path(node.fullpath).suffix.lower() in IMAGE_EXTENSIONS:
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
                if file_type_filter == "image" and ext not in IMAGE_EXTENSIONS:
                    return
                if file_type_filter == "video" and ext not in VIDEO_EXTENSIONS:
                    return
                if file_type_filter == "audio" and ext not in AUDIO_EXTENSIONS:
                    return
                if file_type_filter == "document" and ext not in DOCUMENT_EXTENSIONS:
                    return

            try:
                relative_path = p.relative_to(base_path_obj)
            except ValueError:
                logger.warning(f"Could not determine relative path for {p} against base {base_path_obj}, skipping.")
                return

            info = {'fullpath': node.fullpath, 'metadata': node.metadata.copy()}

            if opts.get('compare_name'):
                info['compare_name'] = node.name

            needs_stat = opts.get('compare_size') or opts.get('compare_date')
            if needs_stat:
                try:
                    stat = p.stat()
                    if opts.get('compare_size'):
                        info['compare_size'] = stat.st_size
                    if opts.get('compare_date'):
                        info['compare_date'] = stat.st_mtime
                except OSError as e:
                    logger.error(f"Could not get stat for file {p}: {e}")

            if opts.get('compare_content_md5'):
                info['compare_content_md5'] = calculate_md5(p)

            if opts.get('compare_histogram'):
                hist = compare_by_histogram.get_histogram(str(p))
                if hist is not None:
                    info['metadata']['histogram'] = hist
            
            if opts.get('compare_llm') and llm_engine and node in llm_files_to_process:
                processed_llm_files += 1
                if progress_callback:
                    progress_message = f"LLM Processing ({processed_llm_files}/{total_llm_files}): {p.name}"
                    progress_callback(progress_message, processed_llm_files)
                
                embedding = llm_engine.get_image_embedding(str(p))
                if embedding is not None:
                    # Convert numpy array to list for JSON serialization
                    info['metadata']['llm_embedding'] = embedding.tolist()


            file_info[relative_path] = info

        elif isinstance(node, FolderNode):
            for child in node.content:
                traverse(child)

    for root_node in structure:
        traverse(root_node)

    return file_info, total_llm_files
