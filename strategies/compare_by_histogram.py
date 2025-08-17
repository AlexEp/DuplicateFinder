import cv2
import numpy as np

# Map UI strings to OpenCV constants
HISTOGRAM_METHODS = {
    'Correlation': cv2.HISTCMP_CORREL,
    'Chi-Square': cv2.HISTCMP_CHISQR,
    'Intersection': cv2.HISTCMP_INTERSECT,
    'Bhattacharyya': cv2.HISTCMP_BHATTACHARYYA
}

# Define which methods measure similarity (higher is better) vs. distance (lower is better)
SIMILARITY_METRICS = ['Correlation', 'Intersection']

def compare(file1_info, file2_info, options):
    """
    Compares two image files based on a selected histogram comparison method.
    """
    path1 = file1_info.get('fullpath')
    path2 = file2_info.get('fullpath')

    # Get method and threshold from options, with sane defaults
    method_name = options.get('histogram_method', 'Correlation')
    try:
        # Threshold is a string from the UI, convert to float
        threshold_str = options.get('histogram_threshold', '0.9')
        threshold = float(threshold_str)
    except (ValueError, TypeError):
        # Fallback if the threshold from UI is invalid
        threshold = 0.9 if method_name in SIMILARITY_METRICS else 0.1

    if not path1 or not path2 or method_name not in HISTOGRAM_METHODS:
        return False

    try:
        img1 = cv2.imread(path1)
        img2 = cv2.imread(path2)

        if img1 is None or img2 is None:
            return False

        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

        h_bins = 50
        s_bins = 60
        histSize = [h_bins, s_bins]
        h_ranges = [0, 180]
        s_ranges = [0, 256]
        ranges = h_ranges + s_ranges
        channels = [0, 1]

        hist1 = cv2.calcHist([hsv1], channels, None, histSize, ranges, accumulate=False)
        cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        hist2 = cv2.calcHist([hsv2], channels, None, histSize, ranges, accumulate=False)
        cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        # Get the correct OpenCV constant for the chosen method
        comparison_method = HISTOGRAM_METHODS[method_name]

        score = cv2.compareHist(hist1, hist2, comparison_method)

        # Apply threshold based on whether it's a similarity or distance metric
        if method_name in SIMILARITY_METRICS:
            return score >= threshold  # For Correlation and Intersection, higher is more similar
        else:
            return score <= threshold  # For Chi-Square and Bhattacharyya, lower is more similar

    except Exception as e:
        print(f"Could not compare histograms for {path1} and {path2}: {e}")
        return False
