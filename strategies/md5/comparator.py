from ..base_comparison_strategy import BaseComparisonStrategy

class CompareByContentMD5(BaseComparisonStrategy):
    @property
    def option_key(self):
        return 'compare_content_md5'

    def compare(self, file1_info, file2_info, opts=None):
        """
        Compares two files based on their MD5 hash.
        Returns False if hash is missing from either file.
        """
        key = 'md5'
        md5_1 = file1_info.get(key)
        md5_2 = file2_info.get(key)

        if md5_1 is not None and md5_2 is not None:
            return md5_1 == md5_2
        return False

    def get_duplications_ids(self, conn, folder_index=None):
        """
        Finds duplicate files based on their MD5 hash.
        """
        cursor = conn.cursor()
        query = """
            SELECT GROUP_CONCAT(f.id)
            FROM files f
            JOIN file_metadata fm ON f.id = fm.file_id
            WHERE (? IS NULL OR f.folder_index = ?)
            GROUP BY fm.md5
            HAVING COUNT(f.id) > 1
        """
        cursor.execute(query, (folder_index, folder_index))

        duplicates = []
        for row in cursor.fetchall():
            duplicates.append([int(id) for id in row[0].split(',')])

        return duplicates
