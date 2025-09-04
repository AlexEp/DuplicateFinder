import cv2
import numpy as np
import json

# Map UI strings to OpenCV constants
HISTOGRAM_METHODS = {
    'Correlation': cv2.HISTCMP_CORREL,
    'Chi-Square': cv2.HISTCMP_CHISQR,
    'Intersection': cv2.HISTCMP_INTERSECT,
    'Bhattacharyya': cv2.HISTCMP_BHATTACHARYYA
}

# Define which methods measure similarity (higher is better) vs. distance (lower is better)
SIMILARITY_METRICS = ['Correlation', 'Intersection']

def get_histogram(path):
    """
    Calculates and returns the normalized HSV histogram for an image file.
    """
    try:
        img = cv2.imread(path)
        if img is None:
            return None

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        h_bins = 50
        s_bins = 60
        histSize = [h_bins, s_bins]
        h_ranges = [0, 180]
        s_ranges = [0, 256]
        ranges = h_ranges + s_ranges
        channels = [0, 1]

        hist = cv2.calcHist([hsv], channels, None, histSize, ranges, accumulate=False)
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist
    except Exception as e:
        print(f"Could not calculate histogram for {path}: {e}")
        return None

def compare(file1_info, file2_info, opts):
    """
    Compares two image files based on a selected histogram comparison method,
    using pre-calculated histograms from file metadata.
    """
    hist1_str = file1_info.get('histogram')
    hist2_str = file2_info.get('histogram')
    method_name = opts.get('histogram_method', 'Correlation')

    if hist1_str is None or hist2_str is None or method_name not in HISTOGRAM_METHODS:
        return None

    try:
        hist1 = np.array(json.loads(hist1_str))
        hist2 = np.array(json.loads(hist2_str))
        comparison_method = HISTOGRAM_METHODS[method_name]
        score = cv2.compareHist(hist1, hist2, comparison_method)

        # Return the score in the specified nested dictionary structure
        return {'histogram_method': {method_name: score}}

    except Exception as e:
        path1 = file1_info.get('fullpath')
        path2 = file2_info.get('fullpath')
        print(f"Could not compare histograms for {path1} and {path2}: {e}")
        return None
