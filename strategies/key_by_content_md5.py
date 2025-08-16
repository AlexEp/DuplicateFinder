def get_key(path, info):
    """Returns the MD5 hash as the key, or None if not present."""
    return info.get('md5')
