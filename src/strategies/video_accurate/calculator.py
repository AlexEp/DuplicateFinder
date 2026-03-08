import cv2
import numpy as np
import logging
from ..base_calculator import BaseCalculator
from config import config

logger = logging.getLogger(__name__)

NUM_FRAMES = 5

class VideoAccurateCalculator(BaseCalculator):
    """
    Extracts multiple frames (N) from a video and calculates their histograms for accurate similarity comparison.
    """
    @property
    def db_key(self):
        return 'hash_accurate'

    def _calculate(self, file_node, opts):
        """
        Calculates the accurate hash of a video file.
        """
        if not opts.get('compare_video_accurate'):
            return None

        # Check if it's a video file based on config
        video_extensions = config.get("file_extensions.video", [])
        if file_node.ext.lower() not in video_extensions:
            return None

        logger.info(f"VideoAccurateCalculator called for {file_node.fullpath}")

        try:
            cap = cv2.VideoCapture(file_node.fullpath)
            if not cap.isOpened():
                return None

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count <= 0:
                cap.release()
                return None

            # Get 5 evenly spaced frames, skipping the very beginning and end to avoid black frames
            step = frame_count // (NUM_FRAMES + 1)
            frame_indices = [step * i for i in range(1, NUM_FRAMES + 1)]

            histograms = []

            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    continue

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
                histograms.append(hist)

            cap.release()

            if not histograms:
                return None

            # If we didn't extract exactly NUM_FRAMES, pad it out or we just store what we have
            # But they should all exist ideally. Just concatenate them.
            # We must be able to unpack them later.
            # Since each histogram is exactly 256*3 floats, we can reshape later.
            all_hists = np.concatenate(histograms)
            return all_hists.tobytes()

        except Exception as e:
            logger.error(f"Could not calculate accurate hash for video {file_node.fullpath}: {e}")
            return None
