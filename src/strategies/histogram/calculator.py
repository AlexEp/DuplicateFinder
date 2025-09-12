import cv2
import numpy as np
from PIL import Image
import logging
from ..base_calculator import BaseCalculator

logger = logging.getLogger(__name__)

class HistogramCalculator(BaseCalculator):
    """
    Calculates image histograms using different methods.
    """
    @property
    def db_key(self):
        return 'histogram'

    def calculate(self, file_node, opts):
        """
        Calculates the histogram of an image file.

        Args:
            file_node (FileNode): The file node to process.
            opts (dict): The options dictionary.

        Returns:
            str: The histogram of the image, or None if an error occurs.
        """
        if not opts.get('compare_histogram'):
            return None

        try:
            with Image.open(file_node.fullpath) as img:
                # Ensure image is in a consistent format
                img = img.convert('RGB')
                # Resize for consistency
                img = img.resize((256, 256))

                # Using numpy to create the histogram
                np_img = np.array(img)

                # Calculate histogram for each channel and concatenate
                hist_r = cv2.calcHist([np_img], [0], None, [256], [0, 256])
                hist_g = cv2.calcHist([np_img], [1], None, [256], [0, 256])
                hist_b = cv2.calcHist([np_img], [2], None, [256], [0, 256])

                # Normalize and concatenate
                cv2.normalize(hist_r, hist_r)
                cv2.normalize(hist_g, hist_g)
                cv2.normalize(hist_b, hist_b)

                # Concatenate histograms
                hist = np.concatenate((hist_r, hist_g, hist_b))

                return hist.tobytes()

        except Exception as e:
            logger.error(f"Could not calculate histogram for {file_node.fullpath}: {e}")
            return None
