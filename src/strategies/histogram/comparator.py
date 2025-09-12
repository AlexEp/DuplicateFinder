import cv2
import numpy as np
from ..base_comparison_strategy import BaseComparisonStrategy

class HistogramComparator(BaseComparisonStrategy):
    """
    Compares image histograms using different methods.
    """
    @property
    def option_key(self):
        return 'compare_histogram'

    @property
    def db_key(self):
        return 'histogram'

    def get_duplicates_query_part(self):
        return "fm.histogram"

    def compare(self, hist1, hist2, method='Correlation'):
        """
        Compares two histograms using the specified method.

        Args:
            hist1 (bytes): The first histogram.
            hist2 (bytes): The second histogram.
            method (str): The comparison method to use.

        Returns:
            float: The similarity score.
        """
        if not hist1 or not hist2:
            return 0.0

        # Convert bytes back to numpy arrays
        hist1 = np.frombuffer(hist1, dtype=np.float32)
        hist2 = np.frombuffer(hist2, dtype=np.float32)

        if method == 'Correlation':
            return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        elif method == 'Chi-Square':
            return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
        elif method == 'Intersection':
            return cv2.compareHist(hist1, hist2, cv2.HISTCMP_INTERSECT)
        elif method == 'Bhattacharyya':
            return cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
        else:
            raise ValueError(f"Unknown histogram comparison method: {method}")
