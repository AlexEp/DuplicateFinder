import hashlib
from pathlib import Path
from models import FileNode, FolderNode
from . import compare_by_histogram

def calculate_md5(file_path):
    """Calculates the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except IOError:
        return None

IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']

def flatten_structure(structure, base_path, opts=None, llm_engine=None, progress_callback=None):
    """
    Flattens the object tree into a dictionary of file info, calculating
    metadata only for the options specified.
    Keys are relative paths to the provided base_path.
    """
    if opts is None:
        opts = {}
    file_info = {}
    base_path_obj = Path(base_path)

    # Get total number of files for progress reporting
    total_files = 0
    def count_files(node):
        nonlocal total_files
        if isinstance(node, FileNode):
            if Path(node.fullpath).suffix.lower() in IMAGE_EXTENSIONS:
                total_files += 1
        elif isinstance(node, FolderNode):
            for child in node.content:
                count_files(child)

    if opts.get('compare_llm') and llm_engine:
        for root_node in structure:
            count_files(root_node)

    processed_files = 0

    def traverse(node):
        nonlocal processed_files
        if isinstance(node, FileNode):
            p = Path(node.fullpath)
            if not p.exists():
                return

            try:
                relative_path = p.relative_to(base_path_obj)
            except ValueError:
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
                except OSError:
                    pass  # Ignore files we can't get stats for

            if opts.get('compare_content_md5'):
                info['compare_content_md5'] = calculate_md5(p)

            if opts.get('compare_histogram'):
                hist = compare_by_histogram.get_histogram(str(p))
                if hist is not None:
                    info['metadata']['histogram'] = hist
            
            if opts.get('compare_llm') and llm_engine and p.suffix.lower() in IMAGE_EXTENSIONS:
                processed_files += 1
                if progress_callback:
                    progress_message = f"LLM Processing ({processed_files}/{total_files}): {p.name}"
                    progress_callback(progress_message)
                
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

    return file_info
