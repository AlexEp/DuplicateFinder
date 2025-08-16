from collections import defaultdict
from . import utils
from . import key_by_name
from . import key_by_date
from . import key_by_size
from . import key_by_content

def run(structure, base_path, opts):
    """
    Finds duplicate files within a single structure.
    This function orchestrates calls to individual key-building strategies.
    """
    if not structure:
        return []

    # Determine if MD5 calculation is needed
    calc_md5 = opts.get('compare_content', False)
    all_files_info = utils.flatten_structure(structure, base_path, calc_md5)

    # Build a list of active key-building strategies based on options
    # Note: The UI calls these 'compare_name', etc. but for duplicates,
    # we are grouping by these attributes.
    active_key_strategies = []
    if opts.get('compare_name'):
        active_key_strategies.append(key_by_name.get_key)
    if opts.get('compare_date'):
        active_key_strategies.append(key_by_date.get_key)
    if opts.get('compare_size'):
        active_key_strategies.append(key_by_size.get_key)
    if opts.get('compare_content'):
        active_key_strategies.append(key_by_content.get_key)

    # Group files by the selected criteria
    groups = defaultdict(list)
    for path, info in all_files_info.items():
        # Build a key based on the selected options
        key_parts = [strategy(path, info) for strategy in active_key_strategies]

        # The key must be a tuple to be hashable
        # and ignore files where a key part couldn't be generated (e.g. no md5)
        if key_parts and None not in key_parts:
            groups[tuple(key_parts)].append(str(path.as_posix()))

    # Filter for groups with more than one file (i.e., duplicates)
    duplicates = [files for files in groups.values() if len(files) > 1]

    return duplicates
