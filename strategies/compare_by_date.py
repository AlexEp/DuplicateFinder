def compare(file1_info, file2_info):
    """Compares two files based on their modification time."""
    return file1_info['mtime'] == file2_info['mtime']
