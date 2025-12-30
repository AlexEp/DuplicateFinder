from ..base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata

class CompareByContentMD5(BaseComparisonStrategy):
    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_content_md5',
            display_name='Content (MD5)',
            description='Compare files by MD5 content hash',
            tooltip='Calculates a unique fingerprint for each file. Slower but ensures exact content matching.',
            requires_calculation=True
        )

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

    def get_duplicates_query_part(self):
        return "fm.md5"

    
