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

    def get_duplications_ids(self, conn, folder_index=None):
        """
        Finds duplicate files based on their name.
        """
        cursor = conn.cursor()
        query = """
            SELECT GROUP_CONCAT(id)
            FROM files
            WHERE name IS NOT NULL AND (? IS NULL OR folder_index = ?)
            GROUP BY name
            HAVING COUNT(id) > 1
        """
        cursor.execute(query, (folder_index, folder_index))

        duplicates = []
        for row in cursor.fetchall():
            duplicates.append([int(id) for id in row[0].split(',')])

        return duplicates
