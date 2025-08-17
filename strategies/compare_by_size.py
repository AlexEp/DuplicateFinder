def compare(file1_info, file2_info):
    """Compares two files based on their size."""
    # The keys must exist because this strategy is only called if compare_size is true.
    return file1_info['compare_size'] == file2_info['compare_size']
