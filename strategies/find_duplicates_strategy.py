from .strategy_registry import get_strategy

def run(conn, opts, folder_index=None):
    """
    Finds duplicate files using the selected strategies.
    """
    all_duplicates = []

    for option, value in opts.get('options', {}).items():
        if value:
            strategy = get_strategy(option)
            if strategy:
                duplicates = strategy.get_duplications_ids(conn, folder_index)
                all_duplicates.extend(duplicates)

    return all_duplicates
