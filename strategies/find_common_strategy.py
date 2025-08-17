from . import utils
from . import compare_by_date
from . import compare_by_size
from . import compare_by_content_md5

def run(structure1, structure2, base_path1, base_path2, opts):
    """
    Finds common files and returns their paths and calculated metadata.
    This function orchestrates calls to individual comparison strategies.
    """
    if not structure1 or not structure2:
        return [], {}, {}

    # Flatten the directory structures into dictionaries, calculating metadata
    info1 = utils.flatten_structure(structure1, base_path1, opts)
    info2 = utils.flatten_structure(structure2, base_path2, opts)

    # Find the common files by relative path
    common_paths = set(info1.keys()).intersection(info2.keys())

    # Build a list of active comparison strategies based on options
    active_strategies = []
    if opts.get('compare_date'):
        active_strategies.append(compare_by_date.compare)
    if opts.get('compare_size'):
        active_strategies.append(compare_by_size.compare)
    if opts.get('compare_content_md5'):
        active_strategies.append(compare_by_content_md5.compare)
    # Note: Histogram comparison is not implemented as a strategy here
    # as it's more complex and its metadata is already gathered in utils.

    matching_paths = []
    for path in common_paths:
        file1_info = info1[path]
        file2_info = info2[path]

        is_match = all(strategy(file1_info, file2_info) for strategy in active_strategies)

        if is_match:
            matching_paths.append(str(path.as_posix()))

    return sorted(matching_paths), info1, info2
