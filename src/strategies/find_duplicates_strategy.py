from .strategy_registry import get_strategy
import database
from pathlib import Path

def run(conn, opts, folder_index=None, file_infos=None):
    """
    Finds duplicate files using a single SQL query based on selected strategies.
    """
    selected_strategies = []
    for option, value in opts.get('options', {}).items():
        if value and option.startswith('compare_'):
            strategy = get_strategy(option)
            if strategy:
                selected_strategies.append(strategy)

    if not selected_strategies:
        return []

    group_by_parts = []
    for strategy in selected_strategies:
        if hasattr(strategy, 'get_duplicates_query_part'):
            group_by_parts.append(strategy.get_duplicates_query_part())
    
    if not group_by_parts:
        return []

    group_by_clause = ", ".join(group_by_parts)

    # Base query
    query = f"""
        SELECT GROUP_CONCAT(f.id)
        FROM files f
        JOIN file_metadata fm ON f.id = fm.file_id
        GROUP BY {group_by_clause}
        HAVING COUNT(f.id) > 1
    """

    # WHERE clause for folder_index
    params = []
    if folder_index is not None:
        if isinstance(folder_index, int):
            folder_index = [folder_index]
        placeholders = ','.join('?' for _ in folder_index)
        query = f"""
            SELECT GROUP_CONCAT(f.id)
            FROM files f
            JOIN file_metadata fm ON f.id = fm.file_id
            WHERE f.folder_index IN ({placeholders})
            GROUP BY {group_by_clause}
            HAVING COUNT(f.id) > 1
        """
        params.extend(folder_index)


    # Execute the query to get groups of duplicate file IDs
    cursor = conn.cursor()
    cursor.execute(query, params)
    duplicate_id_groups = [row[0].split(',') for row in cursor.fetchall()]

    # Fetch file info for each group
    duplicate_groups = []
    for id_group in duplicate_id_groups:
        group_infos = []
        rows = database.get_files_by_ids(conn, id_group)
        if rows:
            columns = [
                'id', 'folder_index', 'path', 'name', 'ext', 'last_seen',
                'size', 'modified_date', 'md5', 'histogram', 'llm_embedding'
            ]
            for row in rows:
                file_info = dict(zip(columns, row))
                
                # Convert path to Path object for consistency
                if isinstance(file_info.get('path'), str):
                    file_info['path'] = Path(file_info['path'])

                group_infos.append(file_info)
        
        if group_infos:
            duplicate_groups.append(group_infos)

    return duplicate_groups