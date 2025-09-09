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
