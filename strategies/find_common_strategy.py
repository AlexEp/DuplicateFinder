from . import utils
from . import compare_by_date
from . import compare_by_size
from . import compare_by_content

def run(structure1, structure2, base_path1, base_path2, opts):
    """
    Finds common files in two structures based on selected criteria.
    This function orchestrates calls to individual comparison strategies.
    """
    if not structure1 or not structure2:
        return []

    # Determine if MD5 calculation is needed
    calc_md5 = opts.get('compare_content', False)

    # Flatten the directory structures into dictionaries
    info1 = utils.flatten_structure(structure1, base_path1, calc_md5)
    info2 = utils.flatten_structure(structure2, base_path2, calc_md5)

    # Find the common files by relative path
    common_paths = set(info1.keys()).intersection(info2.keys())

    # Build a list of active comparison strategies based on options
    active_strategies = []
    if opts.get('compare_date'):
        active_strategies.append(compare_by_date.compare)
    if opts.get('compare_size'):
        active_strategies.append(compare_by_size.compare)
    if opts.get('compare_content'):
        active_strategies.append(compare_by_content.compare)

    results = []
    for path in common_paths:
        file1_info = info1[path]
        file2_info = info2[path]

        # A file is a match if it passes all active comparison strategies
        is_match = all(strategy(file1_info, file2_info) for strategy in active_strategies)

        if is_match:
            results.append(str(path.as_posix()))

    return sorted(results)
