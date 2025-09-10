from ..base_comparison_strategy import BaseComparisonStrategy
from pathlib import Path

class CompareByNameStrategy(BaseComparisonStrategy):
    """Compares two files based on their names."""
    @property
    def option_key(self):
        return 'compare_name'

    def compare(self, file1_info, file2_info, opts=None):
        """
        Compares the names of two files.

        Args:
            file1_info (dict): Metadata for the first file.
            file2_info (dict): Metadata for the second file.
            opts (dict, optional): Options dictionary. Defaults to None.

        Returns:
            bool: True if the file names are the same, False otherwise.
        """
        if 'relative_path' not in file1_info or 'relative_path' not in file2_info:
            return False

        path1 = Path(file1_info.get('relative_path'))
        path2 = Path(file2_info.get('relative_path'))
        return path1.name == path2.name

    @property
    def db_key(self):
        return 'name'

    def get_duplications_ids(self, conn, folder_index=None):
        """
        Finds duplicate files based on their name.
        """
        cursor = conn.cursor()

        # Step 1: Find names that are duplicates
        subquery = """
            SELECT name
            FROM files
            WHERE name IS NOT NULL
            GROUP BY name
            HAVING COUNT(*) > 1
        """
        cursor.execute(subquery)
        duplicate_names = [row[0] for row in cursor.fetchall()]

        if not duplicate_names:
            return []

        # Step 2: For each duplicate name, get the file IDs
        duplicates = []
        for name in duplicate_names:
            query = """
                SELECT id
                FROM files
                WHERE name = ? AND (? IS NULL OR folder_index = ?)
            """
            cursor.execute(query, (name, folder_index, folder_index))
            group = [row[0] for row in cursor.fetchall()]
            if group:
                duplicates.append(group)

        return duplicates
