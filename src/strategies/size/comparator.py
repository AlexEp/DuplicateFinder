from ..base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata

class CompareBySize(BaseComparisonStrategy):
    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_size',
            display_name='Size',
            description='Compare files by size',
            tooltip='Matches files that have the exact same size in bytes.',
            requires_calculation=False
        )

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

    def get_duplicates_query_part(self):
        return "fm.size"

    
