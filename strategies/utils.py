import hashlib
from pathlib import Path
from models import FileNode, FolderNode

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

def flatten_structure(structure, base_path, opts=None):
    """
    Flattens the object tree into a dictionary of file info, calculating
    metadata only for the options specified.
    """
    if opts is None:
        opts = {}
    file_info = {}

    # Need a recursive helper to traverse the tree
    def traverse(node, current_path):
        if isinstance(node, FileNode):
            # Construct the relative path
            relative_path = current_path / node.name

            # Get metadata only if needed
            p = Path(node.fullpath)
            if not p.exists(): return

            info = {}
            # Check if we need to get file stats (for size or date)
            needs_stat = opts.get('compare_size') or opts.get('compare_date')
            if needs_stat:
                stat = p.stat()
                if opts.get('compare_size'):
                    info['size'] = stat.st_size
                if opts.get('compare_date'):
                    info['mtime'] = stat.st_mtime

            # Check if we need to calculate MD5
            if opts.get('compare_content_md5'):
                info['md5'] = calculate_md5(p)

            file_info[relative_path] = info

        elif isinstance(node, FolderNode):
            for child in node.content:
                traverse(child, current_path / node.name)

    # Start traversal from the root of the structure
    for root_node in structure:
        traverse(root_node, Path())

    return file_info
