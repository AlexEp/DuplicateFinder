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
        query = """
            SELECT GROUP_CONCAT(f.id)
            FROM files f
            JOIN file_metadata fm ON f.id = fm.file_id
            WHERE (? IS NULL OR f.folder_index = ?)
            GROUP BY fm.modified_date
            HAVING COUNT(f.id) > 1
        """
        cursor.execute(query, (folder_index, folder_index))

        duplicates = []
        for row in cursor.fetchall():
            duplicates.append([int(id) for id in row[0].split(',')])

        return duplicates
