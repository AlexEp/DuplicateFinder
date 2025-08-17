def compare(file1_info, file2_info):
    """Compares two files based on their MD5 hash."""
    # Ensure both have an MD5 hash and they are equal
    key = 'compare_content_md5'
    if key in file1_info and key in file2_info:
        return file1_info[key] == file2_info[key]
    return False
