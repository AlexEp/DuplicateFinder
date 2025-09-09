from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run(conn, opts, folder_index=None):
    """
    Finds duplicate files using a SQL query.
    """
    if not conn:
        return []

    key_columns = []
    if opts.get('compare_name'):
        key_columns.append('f.name')
    if opts.get('compare_date'):
        key_columns.append('fm.modified_date')
    if opts.get('compare_size'):
        key_columns.append('fm.size')
    if opts.get('compare_content_md5'):
        key_columns.append('fm.md5')

    if not key_columns:
        return []

    group_by_clause = ", ".join(key_columns)
    
    where_clause = ""
    if folder_index is not None:
        where_clause = f"WHERE f.folder_index = {folder_index}"

    # Find groups of duplicates
    query = f"""
        SELECT {group_by_clause}
        FROM files f
        JOIN file_metadata fm ON f.id = fm.file_id
        {where_clause}
        GROUP BY {group_by_clause}
        HAVING COUNT(*) > 1
    """
    
    cursor = conn.cursor()
    logger.info(f"Executing query: {query}")
    cursor.execute(query)
    duplicate_groups_keys = cursor.fetchall()
    logger.info(f"Found {len(duplicate_groups_keys)} duplicate groups.")

    if not duplicate_groups_keys:
        return []

    all_duplicates = []

    # For each group of duplicate keys, get the full file info
    for keys in duplicate_groups_keys:
        where_parts = []
        for i, col in enumerate(key_columns):
            # Handle NULL values
            if keys[i] is None:
                where_parts.append(f"{col} IS NULL")
            else:
                where_parts.append(f"{col} = ?")
        
        where_clause_group = " AND ".join(where_parts)
        if folder_index is not None:
            where_clause_group += f" AND f.folder_index = {folder_index}"

        # Filter out the NULL values from the keys
        filtered_keys = [k for k in keys if k is not None]

        select_query = f"""
            SELECT f.path, f.name, fm.size, f.folder_index
            FROM files f
            JOIN file_metadata fm ON f.id = fm.file_id
            WHERE {where_clause_group}
        """
        
        cursor.execute(select_query, filtered_keys)
        group_files = cursor.fetchall()
        
        group_files_dicts = []
        for row in group_files:
            # We need the base path to construct the full path
            # This is not available in this function, so we'll have to rely on the controller to fix it.
            group_files_dicts.append({
                'relative_path': row[0],
                'name': row[1],
                'size': row[2],
                'folder_index': row[3]
            })
        all_duplicates.append(group_files_dicts)

    return all_duplicates