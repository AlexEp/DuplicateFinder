from .strategy_registry import get_strategy
import database
from pathlib import Path
from config import config

def run(conn, opts, folder_index=None, file_infos=None):
    """
    Finds duplicate files using a single SQL query based on selected strategies,
    and then optionally refines the results with histogram comparison.
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
    histogram_strategy = None
    for strategy in selected_strategies:
        if hasattr(strategy, 'get_duplicates_query_part'):
            if strategy.db_key == 'histogram':
                histogram_strategy = strategy
            else:
                group_by_parts.append(strategy.get_duplicates_query_part())

    duplicate_groups = []
    if group_by_parts:
        group_by_clause = ", ".join(group_by_parts)
        params = []
        where_clauses = []

        # Handle folder_index filter
        if folder_index is not None:
            if isinstance(folder_index, int):
                folder_index = [folder_index]
            placeholders = ','.join('?' for _ in folder_index)
            where_clauses.append(f"f.folder_index IN ({placeholders})")
            params.extend(folder_index)

        # Handle file extension filter
        file_type_filter = opts.get("file_type_filter", "all")
        if file_type_filter != "all":
            extensions = config.get(f"file_extensions.{file_type_filter}", [])
            if extensions:
                ext_placeholders = ','.join('?' for _ in extensions)
                where_clauses.append(f"f.ext IN ({ext_placeholders})")
                params.extend(extensions)

        # Construct the final query
        query = f"""
            SELECT GROUP_CONCAT(f.id)
            FROM files f
            JOIN file_metadata fm ON f.id = fm.file_id
        """
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += f"""
            GROUP BY {group_by_clause}
            HAVING COUNT(f.id) > 1
        """

        # Execute the query to get groups of duplicate file IDs
        cursor = conn.cursor()
        cursor.execute(query, params)
        duplicate_id_groups = [row[0].split(',') for row in cursor.fetchall()]

        # Fetch file info for each group
        for id_group in duplicate_id_groups:
            group_infos = []
            rows = database.get_files_by_ids(conn, id_group)
            if rows:
                columns = [
                    'id', 'folder_index', 'path', 'name', 'ext', 'last_seen',
                    'size', 'modified_date', 'md5', 'llm_embedding'
                ]
                for row in rows:
                    file_info = dict(zip(columns, row))
                    if isinstance(file_info.get('path'), str):
                        file_info['path'] = Path(file_info['path'])
                    group_infos.append(file_info)

            if group_infos:
                duplicate_groups.append(group_infos)
    elif file_infos:
        duplicate_groups = [file_infos]


    if histogram_strategy:
        if not group_by_parts and not file_infos:
            # If only histogram is selected, get all files as a single group
            rows = database.get_all_files(conn, folder_index, file_type_filter=opts.get("file_type_filter", "all"))
            columns = [
                'id', 'folder_index', 'path', 'name', 'ext', 'last_seen',
                'size', 'modified_date', 'md5', 'llm_embedding'
            ]
            file_infos = [dict(zip(columns, row)) for row in rows]
            for info in file_infos:
                if isinstance(info.get('path'), str):
                    info['path'] = Path(info['path'])
            duplicate_groups = [file_infos]

        # Further refine the groups based on histogram similarity
        print("Performing histogram comparison")
        final_groups = []
        for group in duplicate_groups:
            print(f"Processing group: {group}")
            while len(group) > 1:
                file1 = group.pop(0)
                new_group = [file1]
                remaining_files = []
                for file2 in group:
                    hist1 = file1.get('histogram')
                    hist2 = file2.get('histogram')
                    if hist1 and hist2:
                        similarity = histogram_strategy.compare(hist1, hist2, opts.get('histogram_method'))
                        print(f"Similarity between {file1['name']} and {file2['name']}: {similarity}")
                        if similarity >= float(opts.get('histogram_threshold')):
                            new_group.append(file2)
                        else:
                            remaining_files.append(file2)
                    else:
                        remaining_files.append(file2)
                group = remaining_files
                if len(new_group) > 1:
                    final_groups.append(new_group)
        return final_groups

    return duplicate_groups