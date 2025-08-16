def compare(file1_info, file2_info):
    """Compares two files based on their MD5 hash."""
    # Ensure both have an MD5 hash and they are equal
    if 'md5' in file1_info and 'md5' in file2_info:
        return file1_info['md5'] == file2_info['md5']
    return False
