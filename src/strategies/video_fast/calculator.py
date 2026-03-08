import cv2
import numpy as np
import logging
from ..base_calculator import BaseCalculator
from config import config

logger = logging.getLogger(__name__)

class VideoFastCalculator(BaseCalculator):
    """
    Extracts the middle frame of a video and calculates its histogram for fast similarity comparison.
    """
    @property
    def db_key(self):
        return 'hash_fast'

    def _calculate(self, file_node, opts):
        """
        Calculates the fast hash of a video file.
        """
        if not opts.get('compare_video_fast'):
            return None

        # Check if it's a video file based on config
        video_extensions = config.get("file_extensions.video", [])
        if file_node.ext.lower() not in video_extensions:
            return None

        logger.info(f"VideoFastCalculator called for {file_node.fullpath}")

        try:
            cap = cv2.VideoCapture(file_node.fullpath)
            if not cap.isOpened():
                return None

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count <= 0:
                cap.release()
                return None

            # Get the exact middle frame
            middle_frame = frame_count // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                return None

            # Resize for consistency
            frame = cv2.resize(frame, (256, 256))
            
            # Convert BGR to RGB (OpenCV uses BGR by default)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Calculate histogram for each channel and concatenate
            hist_r = cv2.calcHist([frame], [0], None, [256], [0, 256])
            hist_g = cv2.calcHist([frame], [1], None, [256], [0, 256])
            hist_b = cv2.calcHist([frame], [2], None, [256], [0, 256])

            # Normalize and concatenate
            cv2.normalize(hist_r, hist_r)
            cv2.normalize(hist_g, hist_g)
            cv2.normalize(hist_b, hist_b)

            hist = np.concatenate((hist_r, hist_g, hist_b))
            return hist.tobytes()

        except Exception as e:
            logger.error(f"Could not calculate fast hash for video {file_node.fullpath}: {e}")
            return None
