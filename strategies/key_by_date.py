def get_key(path, info):
    """Returns the modification time as the key."""
    return info.get('compare_date')
