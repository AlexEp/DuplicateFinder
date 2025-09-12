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

    
