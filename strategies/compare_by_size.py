import constants

def compare(file1_info, file2_info, opts=None):
    """
    Compares two files based on their size.
    Returns False if size information is missing from either file.
    """
    size1 = file1_info.get(constants.METADATA_SIZE)
    size2 = file2_info.get(constants.METADATA_SIZE)

    if size1 is None or size2 is None:
        return False
    return size1 == size2