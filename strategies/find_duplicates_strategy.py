from .strategy_registry import get_strategy
import database

def run(conn, opts, folder_index=None):
    """
    Finds duplicate files using the first selected strategy.
    """
    selected_strategies = []
    for option, value in opts.items():
        if value and option.startswith('compare_'):
            strategy = get_strategy(option)
            if strategy:
                selected_strategies.append(strategy)

    if not selected_strategies:
        return []

    # Use only the first selected strategy
    first_strategy = selected_strategies[0]
    id_groups = first_strategy.get_duplications_ids(conn, folder_index)

    # Fetch full file info for the duplicate groups
    all_duplicates = []
    for id_group in id_groups:
        file_infos = database.get_files_by_ids(conn, id_group)
        all_duplicates.append(file_infos)

    return all_duplicates
