import hashlib
from pathlib import Path
from models import FileNode, FolderNode
from collections import defaultdict

def _calculate_md5(file_path):
    """Calculates the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except IOError:
        return None

def build_folder_structure(root_path):
    """
    Recursively builds a tree of FileNode and FolderNode objects.
    """
    path_obj = Path(root_path)
    if not path_obj.is_dir():
        return []

    content = []
    for item in sorted(path_obj.iterdir()):
        if item.is_dir():
            folder_node = FolderNode(item)
            folder_node.content = build_folder_structure(item)
            content.append(folder_node)
        elif item.is_file():
            file_node = FileNode(item)
            content.append(file_node)
    return content

def _flatten_structure(structure, base_path, calculate_md5=False):
    """
    Flattens the object tree into a dictionary of file info,
    similar to the old _get_file_info method.
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
            if calculate_md5:
                info["md5"] = _calculate_md5(p)
            file_info[relative_path] = info

        elif isinstance(node, FolderNode):
            for child in node.content:
                traverse(child, current_path / node.name)

    # Start traversal from the root of the structure
    for root_node in structure:
        traverse(root_node, Path())

    return file_info

def find_common_files(structure1, structure2, base_path1, base_path2, opts):
    """
    Finds common files in two pre-built structures based on selected criteria.
    """
    if not structure1 or not structure2:
        return []

    calc_md5 = opts.get('by_content', False)
    info1 = _flatten_structure(structure1, base_path1, calc_md5)
    info2 = _flatten_structure(structure2, base_path2, calc_md5)

    common_names = set(info1.keys()).intersection(info2.keys())

    results = []

    for name in common_names:
        file1_info = info1[name]
        file2_info = info2[name]

        match = True
        if opts.get('by_date') and file1_info['mtime'] != file2_info['mtime']:
            match = False
        if opts.get('by_size') and file1_info['size'] != file2_info['size']:
            match = False
        if opts.get('by_content') and file1_info.get('md5') != file2_info.get('md5'):
            match = False

        if match:
            results.append(str(name.as_posix()))

    return sorted(results)

def find_duplicate_files(structure, base_path, opts):
    """
    Finds duplicate files within a single pre-built structure.
    """
    if not structure:
        return []

    calc_md5 = opts.get('by_content', False)
    all_files_info = _flatten_structure(structure, base_path, calc_md5)

    # Group files by the selected criteria
    groups = defaultdict(list)
    for path, info in all_files_info.items():
        # Build a key based on the selected options
        key_parts = []
        if opts.get('by_name'):
             # Note: finding duplicates by name is only useful across subdirs
            key_parts.append(path.name)
        if opts.get('by_date'):
            key_parts.append(info['mtime'])
        if opts.get('by_size'):
            key_parts.append(info['size'])
        if opts.get('by_content'):
            key_parts.append(info.get('md5'))

        # Use the tuple of key parts as the dictionary key
        if key_parts:
            groups[tuple(key_parts)].append(str(path.as_posix()))

    # Filter for groups with more than one file (i.e., duplicates)
    duplicates = []
    for key, files in groups.items():
        if len(files) > 1:
            duplicates.append(files)

    return duplicates
