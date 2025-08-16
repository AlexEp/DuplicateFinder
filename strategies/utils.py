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

def flatten_structure(structure, base_path, calculate_md5_flag=False):
    """
    Flattens the object tree into a dictionary of file info.
    """
    file_info = {}

    # Need a recursive helper to traverse the tree
    def traverse(node, current_path):
        if isinstance(node, FileNode):
            # Construct the relative path
            relative_path = current_path / node.name

            # Get metadata
            p = Path(node.fullpath)
            if not p.exists(): return

            stat = p.stat()
            info = {
                "size": stat.st_size,
                "mtime": stat.st_mtime
            }
            if calculate_md5_flag:
                info["md5"] = calculate_md5(p)
            file_info[relative_path] = info

        elif isinstance(node, FolderNode):
            for child in node.content:
                traverse(child, current_path / node.name)

    # Start traversal from the root of the structure
    for root_node in structure:
        traverse(root_node, Path())

    return file_info
