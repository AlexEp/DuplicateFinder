import constants

def compare(file1_info, file2_info, opts=None):
    """
    Compares two files based on their modification time.
    Returns False if date information is missing from either file.
    """
    date1 = file1_info.get(constants.METADATA_DATE)
    date2 = file2_info.get(constants.METADATA_DATE)

    if date1 is None or date2 is None:
        return False
    return date1 == date2