from pathlib import Path

def get_key(path_obj, info):
    """Returns the file name from the info dictionary."""
    return info.get('name')
