from .strategy_registry import get_strategy
import database
import itertools

def run(conn, opts, folder_index=None, file_infos=None):
    """
    Finds duplicate files by chaining selected comparison strategies.
    If file_infos is provided, it performs grouping in-memory.
    Otherwise, it fetches data from the database.
    """
    selected_strategies = []
    for option, value in opts.items():
        if value and option.startswith('compare_'):
            strategy = get_strategy(option)
            if strategy:
                selected_strategies.append(strategy)

    if not selected_strategies:
        return []

    # If file_infos are passed directly, use them for in-memory grouping.
    if file_infos:
        current_groups = [file_infos] # Start with one group containing all files
        
        # Refine the groups using ALL selected strategies
        for strategy in selected_strategies:
            next_groups = []
            for group in current_groups:
                if len(group) <= 1:
                    continue

                key_func = lambda info: info.get(strategy.db_key)
                group.sort(key=key_func)

                for key, sub_group_iter in itertools.groupby(group, key=key_func):
                    # Ignore files where the metadata key (e.g., md5) is missing
                    if key is None:
                        continue
                    sub_group = list(sub_group_iter)
                    if len(sub_group) > 1:
                        next_groups.append(sub_group)
            current_groups = next_groups
        return current_groups

    # --- Legacy DB-path (if file_infos not provided) ---
    # Step 1: Get initial groups from DB using the first strategy (e.g., size)
    first_strategy = selected_strategies[0]
    id_groups = first_strategy.get_duplications_ids(conn, folder_index)

    if not id_groups:
        return []

    # If only one strategy was selected, we are done with grouping.
    if len(selected_strategies) == 1:
        all_duplicates = []
        for id_group in id_groups:
            if len(id_group) > 1:
                file_infos = database.get_files_by_ids(conn, id_group)
                all_duplicates.append(file_infos)
        return all_duplicates

    # Step 2: If multiple strategies, refine the groups in Python.
    # Fetch file info for all potential duplicates from the first pass.
    all_ids = [id for group in id_groups for id in group]
    all_file_infos = database.get_files_by_ids(conn, all_ids)
    infos_by_id = {info['id']: info for info in all_file_infos}

    # Create initial groups of file_info objects based on the first strategy's results
    initial_groups = []
    for id_group in id_groups:
        initial_groups.append([infos_by_id[id] for id in id_group if id in infos_by_id])

    # Step 3: Iteratively refine the groups using the subsequent strategies
    current_groups = initial_groups
    for strategy in selected_strategies[1:]:
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
