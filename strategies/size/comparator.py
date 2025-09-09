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
