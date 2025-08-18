def get_key(path, info):
    """Returns the file size as the key."""
    return info.get('compare_size')
