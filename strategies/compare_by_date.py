def compare(file1_info, file2_info):
    """
    Compares two files based on their modification time.
    Returns False if date information is missing from either file.
    """
    key = 'compare_date'
    if key not in file1_info or key not in file2_info:
        return False
    return file1_info[key] == file2_info[key]
