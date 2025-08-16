import hashlib
from pathlib import Path

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

def _get_file_info(folder_path, recursive, calculate_md5=False):
    """
    Gathers information about each file in a directory.
    Returns a dictionary mapping relative paths to their info.
    """
    base_path = Path(folder_path)
    if not base_path.is_dir():
        return {}

    file_info = {}

    if recursive:
        file_iterator = base_path.rglob('*')
    else:
        file_iterator = base_path.iterdir()

    for item in file_iterator:
        if item.is_file():
            relative_path = item.relative_to(base_path)
            stat = item.stat()
            info = {
                "size": stat.st_size,
                "mtime": stat.st_mtime
            }
            if calculate_md5:
                info["md5"] = _calculate_md5(item)
            file_info[relative_path] = info

    return file_info

def find_common_files(folder1, folder2, opts):
    """
    Finds common files in two folders based on selected criteria.
    """
    if not folder1 or not folder2 or not Path(folder1).is_dir() or not Path(folder2).is_dir():
        return []

    # Get file information for both folders
    # Only calculate MD5 if the user has requested it
    calc_md5 = opts.get('by_content', False)
    info1 = _get_file_info(folder1, opts['recursive'], calc_md5)
    info2 = _get_file_info(folder2, opts['recursive'], calc_md5)

    # Find the intersection of file names (relative paths)
    common_names = set(info1.keys()).intersection(info2.keys())

    results = []

    for name in common_names:
        file1_info = info1[name]
        file2_info = info2[name]

        # Check against selected criteria
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
