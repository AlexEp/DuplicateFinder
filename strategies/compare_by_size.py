def compare(file1_info, file2_info):
    """
    Compares two files based on their size.
    Returns False if size information is missing from either file.
    """
    key = 'compare_size'
    if key not in file1_info or key not in file2_info:
        return False
    return file1_info[key] == file2_info[key]
