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

    @property
    def db_key(self):
        return 'md5'

    def get_duplications_ids(self, conn, folder_index=None):
        """
        Finds duplicate files based on their MD5 hash.
        """
        cursor = conn.cursor()

        # Step 1: Find MD5 hashes that are duplicates
        subquery = """
            SELECT md5
            FROM file_metadata
            WHERE md5 IS NOT NULL
            GROUP BY md5
            HAVING COUNT(*) > 1
        """
        cursor.execute(subquery)
        duplicate_md5s = [row[0] for row in cursor.fetchall()]

        if not duplicate_md5s:
            return []

        # Step 2: For each duplicate hash, get the file IDs
        duplicates = []
        for md5 in duplicate_md5s:
            query = """
                SELECT f.id
                FROM files f
                JOIN file_metadata fm ON f.id = fm.file_id
                WHERE fm.md5 = ? AND (? IS NULL OR f.folder_index = ?)
            """
            cursor.execute(query, (md5, folder_index, folder_index))
            group = [row[0] for row in cursor.fetchall()]
            if group:
                duplicates.append(group)

        return duplicates
