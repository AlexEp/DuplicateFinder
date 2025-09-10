from ..base_comparison_strategy import BaseComparisonStrategy

class CompareByDate(BaseComparisonStrategy):
    @property
    def option_key(self):
        return 'compare_date'

    def compare(self, file1_info, file2_info, opts=None):
        """
        Compares two files based on their modification time.
        Returns False if date information is missing from either file.
        """
        key = 'modified_date'
        if key not in file1_info or key not in file2_info:
            return False
        return file1_info[key] == file2_info[key]

    def get_duplications_ids(self, conn, folder_index=None):
        """
        Finds duplicate files based on their modification date.
        """
        cursor = conn.cursor()

        # Step 1: Find dates that are duplicates
        subquery = """
            SELECT modified_date
            FROM file_metadata
            GROUP BY modified_date
            HAVING COUNT(*) > 1
        """
        cursor.execute(subquery)
        duplicate_dates = [row[0] for row in cursor.fetchall()]

        if not duplicate_dates:
            return []

        # Step 2: For each duplicate date, get the file IDs
        duplicates = []
        for date in duplicate_dates:
            query = """
                SELECT f.id
                FROM files f
                JOIN file_metadata fm ON f.id = fm.file_id
                WHERE fm.modified_date = ? AND (? IS NULL OR f.folder_index = ?)
            """
            cursor.execute(query, (date, folder_index, folder_index))
            group = [row[0] for row in cursor.fetchall()]
            if group:
                duplicates.append(group)

        return duplicates
