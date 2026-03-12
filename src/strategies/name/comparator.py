import difflib
from pathlib import Path
from ..base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata


class CompareByNameStrategy(BaseComparisonStrategy):
    """
    Compares two files based on their filenames.
    Supports both exact matching (100% threshold) and fuzzy similarity matching.
    Uses difflib.SequenceMatcher for fuzzy comparison — no extra dependencies required.
    """

    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_name',
            display_name='Name',
            description='Compare files by filename similarity',
            tooltip=(
                'Matches files that have similar filenames.\n'
                '100% = exact name match (fastest).\n'
                'Lower values allow fuzzy/partial name matching.'
            ),
            requires_calculation=False,
            has_threshold=True,
            threshold_label='Name Similarity %:',
            default_threshold=1.0
        )

    @property
    def is_similarity_strategy(self):
        """Always use pairwise comparison so both exact and fuzzy modes work correctly."""
        return True

    @property
    def option_key(self):
        return 'compare_name'

    @property
    def db_key(self):
        return 'name'

    def _get_stem(self, file_info: dict) -> str:
        """Returns the filename stem (no extension) for comparison."""
        name = file_info.get('name', '')
        if name:
            return Path(name).stem
        # Fallback: derive from relative_path if present
        rel = file_info.get('relative_path', '')
        if rel:
            return Path(rel).stem
        return ''

    def compare(self, file1_info: dict, file2_info: dict, opts=None) -> bool:
        """
        Compares two files by name similarity.

        Args:
            file1_info: Metadata dict for the first file.
            file2_info: Metadata dict for the second file.
            opts:       Options dictionary; reads 'compare_name_threshold' key
                        (float 0.0–1.0, default 1.0).

        Returns:
            True if the name similarity ratio >= threshold.
        """
        threshold = 1.0
        if opts:
            try:
                threshold = float(opts.get('compare_name_threshold', 1.0))
            except (ValueError, TypeError):
                threshold = 1.0

        stem1 = self._get_stem(file1_info).lower()
        stem2 = self._get_stem(file2_info).lower()

        if not stem1 or not stem2:
            return False

        if threshold >= 1.0:
            # Fast exact comparison — no need for SequenceMatcher overhead
            return stem1 == stem2

        ratio = difflib.SequenceMatcher(None, stem1, stem2).ratio()
        return ratio >= threshold

    def get_duplicates_query_part(self):
        # Kept for registry compatibility; not used because is_similarity_strategy=True
        return 'f.name'
