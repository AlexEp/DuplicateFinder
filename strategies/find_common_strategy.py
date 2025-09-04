from . import utils
from . import compare_by_date
from . import compare_by_size
from . import compare_by_content_md5
from . import compare_by_llm

def run(info1, info2, opts):
    """
    Finds common files in two metadata dictionaries based on selected criteria.
    This function orchestrates calls to individual comparison strategies.
    """
    if not info1 or not info2:
        return []

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
    if opts.get('compare_llm'):
        # Use the dedicated LLM similarity threshold from the options.
        try:
            threshold = float(opts.get('llm_similarity_threshold', 0.8))
        except (ValueError, TypeError):
            threshold = 0.8 # Default value in case of invalid data
        active_strategies.append(
            lambda f1, f2: compare_by_llm.compare(f1, f2, threshold)[0]
        )

    matching_files = []
    for path in common_paths:
        file1_info = info1[path]
        file2_info = info2[path]

        # A file is a match if it passes all active comparison strategies
        is_match = all(strategy(file1_info, file2_info) for strategy in active_strategies)

        if is_match:
            # Add relative path to the dictionary for easier access later
            file1_info['relative_path'] = str(path)
            matching_files.append(file1_info)

    return sorted(matching_files, key=lambda f: f['relative_path'])
