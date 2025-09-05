from collections import defaultdict
import itertools
from pathlib import Path
from . import key_by_name, key_by_date, key_by_size, key_by_content_md5
from . import compare_by_histogram, compare_by_llm
from utils.graph_utils import find_connected_components
import constants

def _initialize_file_info(all_files_info, base_path):
    fullpath_to_info = {}
    base_path_obj = Path(base_path) if base_path else None
    for path, info in all_files_info.items():
        info[constants.METADATA_RELATIVE_PATH] = str(path)
        info[constants.METADATA_FULLPATH] = str(base_path_obj / path) if base_path_obj else str(path)
        fullpath_to_info[info[constants.METADATA_FULLPATH]] = info
    return fullpath_to_info

def _get_active_key_strategies(opts):
    strategy_map = {
        constants.COMPARE_NAME: key_by_name.get_key,
        constants.COMPARE_DATE: key_by_date.get_key,
        constants.COMPARE_SIZE: key_by_size.get_key,
        constants.COMPARE_CONTENT_MD5: key_by_content_md5.get_key,
    }
    return [strategy for opt, strategy in strategy_map.items() if opts.get(opt)]

def _group_files(all_files_info, active_key_strategies, use_histogram):
    groups = defaultdict(list)
    if not active_key_strategies and use_histogram:
        groups[constants.ALL_FILES_GROUP_KEY] = list(all_files_info.values())
    else:
        for info in all_files_info.values():
            path_obj = Path(info[constants.METADATA_RELATIVE_PATH])
            key_parts = [strategy(path_obj, info) for strategy in active_key_strategies]
            if key_parts and None not in key_parts:
                groups[tuple(key_parts)].append(info)
    return [infos for infos in groups.values() if len(infos) > 1]

def _create_histogram_comparator(opts):
    def histogram_comparator(f1, f2):
        comparison_result = compare_by_histogram.compare(f1, f2, opts)
        if not comparison_result or constants.HISTOGRAM_METHOD not in comparison_result:
            return False

        method_name, score = list(comparison_result[constants.HISTOGRAM_METHOD].items())[0]
        try:
            threshold = float(opts.get(constants.HISTOGRAM_THRESHOLD, constants.DEFAULT_HISTOGRAM_THRESHOLD))
        except (ValueError, TypeError):
            threshold = constants.DEFAULT_HISTOGRAM_THRESHOLD if method_name in constants.SIMILARITY_METRICS else constants.DEFAULT_DISTANCE_THRESHOLD

        return score >= threshold if method_name in constants.SIMILARITY_METRICS else score <= threshold
    return histogram_comparator

def _create_llm_comparator(opts):
    try:
        llm_threshold = float(opts.get(constants.LLM_SIMILARITY_THRESHOLD, constants.DEFAULT_LLM_SIMILARITY_THRESHOLD))
    except (ValueError, TypeError):
        llm_threshold = constants.DEFAULT_LLM_SIMILARITY_THRESHOLD
    return lambda f1, f2: compare_by_llm.compare(f1, f2, llm_threshold)[0]

def _get_comparison_strategies(opts):
    strategies = []
    if opts.get(constants.COMPARE_HISTOGRAM):
        strategies.append(_create_histogram_comparator(opts))
    if opts.get(constants.COMPARE_LLM):
        strategies.append(_create_llm_comparator(opts))
    return strategies

def _find_duplicate_sets(potential_duplicate_groups, comparison_strategies, fullpath_to_info):
    final_duplicates = []
    for group in potential_duplicate_groups:
        adj_list = defaultdict(list)
        nodes_in_group = [info[constants.METADATA_FULLPATH] for info in group]

        for info1, info2 in itertools.combinations(group, 2):
            if all(strategy(info1, info2) for strategy in comparison_strategies):
                path1, path2 = info1[constants.METADATA_FULLPATH], info2[constants.METADATA_FULLPATH]
                adj_list[path1].append(path2)
                adj_list[path2].append(path1)

        components = find_connected_components(nodes_in_group, adj_list)
        for component in components:
            if len(component) > 1:
                final_duplicates.append([fullpath_to_info[path] for path in component])
    return final_duplicates

def run(all_files_info, opts, base_path=None):
    if not all_files_info:
        return []

    fullpath_to_info = _initialize_file_info(all_files_info, base_path)
    active_key_strategies = _get_active_key_strategies(opts)

    use_histogram_only = opts.get(constants.COMPARE_HISTOGRAM) and not active_key_strategies
    if not active_key_strategies and not use_histogram_only:
        return []

    potential_duplicate_groups = _group_files(all_files_info, active_key_strategies, use_histogram_only)
    comparison_strategies = _get_comparison_strategies(opts)

    if not comparison_strategies:
        return potential_duplicate_groups

    return _find_duplicate_sets(potential_duplicate_groups, comparison_strategies, fullpath_to_info)
