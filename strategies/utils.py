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
    Keys are relative paths to the provided base_path.
    """
    if opts is None:
        opts = {}
    file_info = {}
    base_path_obj = Path(base_path)

    def traverse(node):
        if isinstance(node, FileNode):
            p = Path(node.fullpath)
            if not p.exists():
                return

            try:
                relative_path = p.relative_to(base_path_obj)
            except ValueError:
                return

            info = {'fullpath': node.fullpath}

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
                info['histogram_method'] = opts.get('histogram_method')
                info['histogram_threshold'] = opts.get('histogram_threshold')

            file_info[relative_path] = info

        elif isinstance(node, FolderNode):
            for child in node.content:
                traverse(child)

    for root_node in structure:
        traverse(root_node)

    return file_info
