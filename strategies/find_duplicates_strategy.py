from collections import defaultdict
import itertools
import json
from . import utils
from . import key_by_name
from . import key_by_date
from . import key_by_size
from . import key_by_content_md5
from . import compare_by_histogram
from . import compare_by_llm

def _find_connected_components(nodes, adj_list):
    """Finds all connected components in a graph using a basic traversal."""
    visited = set()
    components = []
    for node in nodes:
        if node not in visited:
            component = []
            q = [node]
            visited.add(node)
            head = 0
            while head < len(q):
                u = q[head]
                head += 1
                component.append(u)
                if u in adj_list:
                    for v in adj_list[u]:
                        if v not in visited:
                            visited.add(v)
                            q.append(v)
            components.append(component)
    return components

def run(all_files_info, opts):
    """
    Finds duplicate files within a single metadata dictionary.
    This function orchestrates calls to individual key-building strategies
    and can optionally apply a secondary, pairwise comparison.
    """
    if not all_files_info:
        return []

    # Create a lookup from fullpath to info dict for later, and add relative_path
    fullpath_to_info = {}
    for path, info in all_files_info.items():
        info['relative_path'] = str(path.as_posix())
        fullpath_to_info[info['fullpath']] = info

    # --- Phase 1: Grouping by Keys ---

    active_key_strategies = []
    if opts.get('compare_name'):
        active_key_strategies.append(key_by_name.get_key)
    if opts.get('compare_date'):
        active_key_strategies.append(key_by_date.get_key)
    if opts.get('compare_size'):
        active_key_strategies.append(key_by_size.get_key)
    if opts.get('compare_content_md5'):
        active_key_strategies.append(key_by_content_md5.get_key)

    # If no strategies are selected, we can't find duplicates.
    if not active_key_strategies and not opts.get('compare_histogram'):
        return []

    groups = defaultdict(list)
    # If we are only doing histogram, group all files together.
    # Otherwise, group by the selected keying strategies.
    if not active_key_strategies and opts.get('compare_histogram'):
         # Note: This will be very slow for large numbers of files.
         # It's better to use histogram with a keying strategy (like size).
        groups['all_files'] = list(all_files_info.values())
    else:
        for path, info in all_files_info.items():
            key_parts = [strategy(path, info) for strategy in active_key_strategies]
            if key_parts and None not in key_parts:
                groups[tuple(key_parts)].append(info)

    potential_duplicate_groups = [infos for infos in groups.values() if len(infos) > 1]

    # --- Phase 2: Pairwise Comparisons (Histogram, LLM, etc.) ---
    comparison_strategies = []
    if opts.get('compare_histogram'):
        def histogram_comparator(f1, f2):
            SIMILARITY_METRICS = ['Correlation', 'Intersection']
            comparison_result = compare_by_histogram.compare(f1, f2, opts)
            if not comparison_result or 'histogram_method' not in comparison_result:
                return False
            
            method_name, score = list(comparison_result['histogram_method'].items())[0]
            try:
                threshold = float(opts.get('histogram_threshold', '0.9'))
            except (ValueError, TypeError):
                threshold = 0.9 if method_name in SIMILARITY_METRICS else 0.1
            
            if method_name in SIMILARITY_METRICS:
                return score >= threshold
            else: # distance metric
                return score <= threshold
        comparison_strategies.append(histogram_comparator)

    if opts.get('compare_llm'):
        llm_settings = {}
        try:
            with open("llm_settings.json", "r") as f:
                llm_settings = json.load(f)
        except (IOError, json.JSONDecodeError):
            pass # Use default
        
        llm_threshold = llm_settings.get("similarity_threshold", 90.0)

        comparison_strategies.append(
            lambda f1, f2: compare_by_llm.compare(f1, f2, llm_threshold)[0]
        )

    if not comparison_strategies:
        return [group for group in potential_duplicate_groups]

    final_duplicates = []
    for group in potential_duplicate_groups:
        adj_list = defaultdict(list)
        nodes_in_group = [info['fullpath'] for info in group]

        for info1, info2 in itertools.combinations(group, 2):
            # A pair is a match if it passes ALL pairwise comparison strategies
            is_match = all(strategy(info1, info2) for strategy in comparison_strategies)
            
            if is_match:
                path1 = info1['fullpath']
                path2 = info2['fullpath']
                adj_list[path1].append(path2)
                adj_list[path2].append(path1)

        # For these comparisons, we build a graph where nodes are file paths
        # and an edge exists if two files are similar enough. After building the graph,
        # find all connected components. Each component is a set of files that are
        # all duplicates of each other.
        components = _find_connected_components(nodes_in_group, adj_list)

        # Only keep components with more than one file (actual duplicates)
        for component in components:
            if len(component) > 1:
                # The component is a list of full file paths.
                # We use the fullpath_to_info map created at the start of the function
                # to convert these paths back into the info dictionaries the UI expects.
                final_duplicates.append([fullpath_to_info[path] for path in component])

    return final_duplicates
