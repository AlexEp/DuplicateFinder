from . import strategy_registry

def run(info1, info2, opts):
    """
    Finds common files in two metadata dictionaries based on selected criteria.
    This function orchestrates calls to individual comparison strategies using the strategy registry.
    """
    if not info1 or not info2:
        return []

    common_paths = set(info1.keys()).intersection(info2.keys())
    active_strategies = strategy_registry.get_active_strategies(opts)

    if not active_strategies:
        return []

    matching_files = []
    for path in common_paths:
        file1_info = info1[path]
        file2_info = info2[path]

        is_match = all(strategy(file1_info, file2_info, opts) for strategy in active_strategies)

        if is_match:
            file1_info['relative_path'] = str(path)
            matching_files.append(file1_info)

    return sorted(matching_files, key=lambda f: f['relative_path'])