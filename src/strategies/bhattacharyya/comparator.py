import cv2
import numpy as np
from ..base_comparison_strategy import BaseComparisonStrategy

class BhattacharyyaHistogramComparator(BaseComparisonStrategy):
    """
    Compares image histograms using bhattacharyya.
    """
    @property
    def option_key(self):
        return 'compare_histogram_bhattacharyya'

    @property
    def db_key(self):
        return 'histogram_bhattacharyya'

    def get_duplicates_query_part(self):
        return "fm.histogram_bhattacharyya"

    def compare(self, hist1, hist2, method=None):
        """
        Compares two histograms using bhattacharyya.

        Args:
            hist1 (bytes): The first histogram.
            hist2 (bytes): The second histogram.
            method (str): The comparison method to use (ignored).

        Returns:
            float: The similarity score.
        """
        if not hist1 or not hist2:
            return 0.0

        # Convert bytes back to numpy arrays
        hist1 = np.frombuffer(hist1, dtype=np.float32)
        hist2 = np.frombuffer(hist2, dtype=np.float32)

        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
