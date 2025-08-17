def compare(file1_info, file2_info):
    """
    Compares two files based on their MD5 hash.
    Returns False if hash is missing from either file.
    """
    key = 'compare_content_md5'
    if key in file1_info and key in file2_info:
        # Also check that the hash calculation didn't fail (is not None)
        if file1_info[key] is not None and file2_info[key] is not None:
            return file1_info[key] == file2_info[key]
    return False
