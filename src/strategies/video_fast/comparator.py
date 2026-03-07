import cv2
import numpy as np
from ..base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata
from config import config

class VideoFastComparator(BaseComparisonStrategy):
    """
    Compares videos using the middle frame's histogram for fast similarity matching.
    """
    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_video_fast',
            display_name='Video Fast (Middle Frame)',
            description='Compare videos by middle frame histogram',
            tooltip='Fastest method for identical videos. Only extracts one central frame. Suitable for identical videos of different resolutions/formats.',
            requires_calculation=True,
            has_threshold=True,
            threshold_label='Similarity Threshold:',
            default_threshold=0.9
        )

    @property
    def is_similarity_strategy(self):
        return True

    @property
    def option_key(self):
        return 'compare_video_fast'

    @property
    def db_key(self):
        return 'hash_fast'

    def get_duplicates_query_part(self):
        return "fm.hash_fast"

    def compare(self, file1, file2, opts=None):
        """
        Compares two fast video hashes.
        """
        hash1 = file1.get('hash_fast')
        hash2 = file2.get('hash_fast')

        if not hash1 or not hash2:
            return False

        # Convert bytes back to numpy arrays
        hash1 = np.frombuffer(hash1, dtype=np.float32)
        hash2 = np.frombuffer(hash2, dtype=np.float32)

        # Correlation logic is generally best for color histograms
        similarity = cv2.compareHist(hash1, hash2, cv2.HISTCMP_CORREL)

        threshold = float(opts.get('compare_video_fast_threshold', 0.9)) if opts else 0.9
        return similarity >= threshold
