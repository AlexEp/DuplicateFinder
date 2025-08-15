from pathlib import Path

def _get_files(folder_path, recursive):
    """Generator to yield files from a directory as relative paths."""
    base_path = Path(folder_path)
    if not base_path.is_dir():
        return

    if recursive:
        for item in base_path.rglob('*'):
            if item.is_file():
                yield item.relative_to(base_path)
    else:
        for item in base_path.iterdir():
            if item.is_file():
                yield item.relative_to(base_path)

def find_common_files(folder1, folder2, recursive):
    """
    Finds common files in two folders based on their names.

    Args:
        folder1 (str): Path to the first folder.
        folder2 (str): Path to the second folder.
        recursive (bool): Whether to search in subdirectories.

    Returns:
        list: A sorted list of common file paths (as strings).
    """
    if not folder1 or not folder2 or not Path(folder1).is_dir() or not Path(folder2).is_dir():
        return []

    files1 = set(_get_files(folder1, recursive))
    files2 = set(_get_files(folder2, recursive))

    common_files_paths = sorted(list(files1.intersection(files2)))

    # Convert Path objects to strings for easier use in the UI
    return [str(p.as_posix()) for p in common_files_paths]
