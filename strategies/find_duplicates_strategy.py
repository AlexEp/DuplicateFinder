from .strategy_registry import get_strategy
import database
import itertools
from pathlib import Path


def run(conn, opts, folder_index=None, file_infos=None):
    """
    Finds duplicate files by chaining selected comparison strategies.
    If file_infos is provided, it performs grouping in-memory.
    Otherwise, it fetches data from the database for the given folder_index.
    """
    selected_strategies = []
    for option, value in opts.get('options', {}).items():
        if value and option.startswith('compare_'):
            strategy = get_strategy(option)
            if strategy:
                selected_strategies.append(strategy)

    if not selected_strategies:
        return []

    # If file_infos are not provided, fetch them from the database.
    if file_infos is None:
        if folder_index is None:
            return []
        rows = database.get_all_files(conn, folder_index)
        columns = [
            'id', 'folder_index', 'path', 'name', 'ext', 'last_seen',
            'size', 'modified_date', 'md5', 'histogram', 'llm_embedding'
        ]
        file_infos = [dict(zip(columns, row)) for row in rows]
        # Convert path to Path object for consistency
        for info in file_infos:
            if isinstance(info.get('path'), str):
                info['path'] = Path(info['path'])


    current_groups = [file_infos]

    for strategy in selected_strategies:
        next_groups = []
        for group in current_groups:
            if len(group) <= 1:
                continue

            key_func = lambda info: info.get(strategy.db_key)
            group.sort(key=key_func)

            for key, sub_group_iter in itertools.groupby(group, key=key_func):
                if key is None:
                    continue
                
                sub_group = list(sub_group_iter)
                
                if len(sub_group) > 1:
                    next_groups.append(sub_group)
        
        current_groups = next_groups
        
    return current_groups
