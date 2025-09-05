import constants

def compare(file1_info, file2_info, opts=None):
    """
    Compares two files based on their MD5 hash.
    Returns False if hash is missing from either file.
    """
    md5_1 = file1_info.get(constants.METADATA_MD5)
    md5_2 = file2_info.get(constants.METADATA_MD5)

    if md5_1 is not None and md5_2 is not None:
        return md5_1 == md5_2
    return False