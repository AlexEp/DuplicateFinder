from .strategy_registry import get_strategy
import database

def run(conn, opts, folder_index=None):
    """
    Finds duplicate files using the selected strategies.
    """
    all_duplicate_ids = []

    for option, value in opts.get('options', {}).items():
        if value:
            strategy = get_strategy(option)
            if strategy:
                duplicate_ids = strategy.get_duplications_ids(conn, folder_index)
                all_duplicate_ids.extend(duplicate_ids)

    all_duplicates = []
    for id_group in all_duplicate_ids:
        files_data = database.get_files_by_ids(conn, id_group)
        file_infos = []
        for file_data in files_data:
            file_id, f_index, path, name, ext, _, size, modified_date, md5, histogram, llm_embedding = file_data
            file_infos.append({
                'id': file_id,
                'folder_index': f_index,
                'relative_path': path,
                'name': name,
                'ext': ext,
                'size': size,
                'modified_date': modified_date,
                'md5': md5,
                'histogram': histogram,
                'llm_embedding': llm_embedding
            })
        all_duplicates.append(file_infos)

    return all_duplicates
