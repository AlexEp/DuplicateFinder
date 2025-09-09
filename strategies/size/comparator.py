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

    def get_duplications_ids(self, conn, folder_index=None):
        """
        Finds duplicate files based on their size.
        """
        cursor = conn.cursor()
        query = """
            SELECT GROUP_CONCAT(f.id)
            FROM files f
            JOIN file_metadata fm ON f.id = fm.file_id
            WHERE (? IS NULL OR f.folder_index = ?)
            GROUP BY fm.size
            HAVING COUNT(f.id) > 1
        """
        cursor.execute(query, (folder_index, folder_index))

        duplicates = []
        for row in cursor.fetchall():
            duplicates.append([int(id) for id in row[0].split(',')])

        return duplicates
