from ..base_comparison_strategy import BaseComparisonStrategy

class CompareBySize(BaseComparisonStrategy):
    @property
    def option_key(self):
        return 'compare_size'

    def compare(self, file1_info, file2_info, opts=None):
        """
        Compares two files based on their size.
        Returns False if size information is missing from either file.
        """
        key = 'size'
        if key not in file1_info or key not in file2_info:
            return False
        return file1_info[key] == file2_info[key]

    @property
    def db_key(self):
        return 'size'

    def get_duplications_ids(self, conn, folder_index=None):
        """
        Finds duplicate files based on their size.
        """
        cursor = conn.cursor()

        # Step 1: Find sizes that are duplicates
        subquery = """
            SELECT size
            FROM file_metadata
            WHERE size IS NOT NULL
            GROUP BY size
            HAVING COUNT(*) > 1
        """
        cursor.execute(subquery)
        duplicate_sizes = [row[0] for row in cursor.fetchall()]

        if not duplicate_sizes:
            return []

        # Step 2: For each duplicate size, get the file IDs
        duplicates = []
        for size in duplicate_sizes:
            query = """
                SELECT f.id
                FROM files f
                JOIN file_metadata fm ON f.id = fm.file_id
                WHERE fm.size = ? AND (? IS NULL OR f.folder_index = ?)
            """
            cursor.execute(query, (size, folder_index, folder_index))
            group = [row[0] for row in cursor.fetchall()]
            if group:
                duplicates.append(group)

        return duplicates
