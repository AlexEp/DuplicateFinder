from ..base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata

class CompareByDate(BaseComparisonStrategy):
    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_date',
            display_name='Date',
            description='Compare files by modification date',
            tooltip='Matches files that were last modified at the exact same time.',
            requires_calculation=False
        )

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

    @property
    def db_key(self):
        return 'modified_date'

    def get_duplicates_query_part(self):
        return "fm.modified_date"

    
