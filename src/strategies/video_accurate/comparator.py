import cv2
import numpy as np
import logging
from ..base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata
from config import config

logger = logging.getLogger(__name__)

# Same number of features per histogram as we extract in calculator
FEATURES_PER_HIST = 256 * 3

class VideoAccurateComparator(BaseComparisonStrategy):
    """
    Compares videos using multiple frame histograms for an accurate percentage match.
    """
    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_video_accurate',
            display_name='Video Accurate (% Match)',
            description='Compare videos by multiple frames',
            tooltip='Accurate method that checks multiple frames throughout the video. Uses a threshold representing the percentage of frames that must match (default 100%).',
            requires_calculation=True,
            has_threshold=True,
            threshold_label='Match Percentage:',
            default_threshold=1.0 # default 100%
        )

    @property
    def is_similarity_strategy(self):
        return True

    @property
    def option_key(self):
        return 'compare_video_accurate'

    @property
    def db_key(self):
        return 'hash_accurate'

    def get_duplicates_query_part(self):
        return "fm.hash_accurate"

    def compare(self, file1, file2, opts=None):
        """
        Compares two accurate video hashes based on percentage of matching frames.
        """
        hash1 = file1.get('hash_accurate')
        hash2 = file2.get('hash_accurate')

        if not hash1 or not hash2:
            return False

        try:
            # Convert bytes back to numpy arrays
            arr1 = np.frombuffer(hash1, dtype=np.float32)
            arr2 = np.frombuffer(hash2, dtype=np.float32)

            # Reshape into individual frames (each frame has FEATURES_PER_HIST floats)
            num_frames1 = len(arr1) // FEATURES_PER_HIST
            num_frames2 = len(arr2) // FEATURES_PER_HIST

            if num_frames1 == 0 or num_frames2 == 0:
                return False

            frames1 = arr1.reshape(num_frames1, FEATURES_PER_HIST)
            frames2 = arr2.reshape(num_frames2, FEATURES_PER_HIST)

            # We consider a frame pair to "match" if correlation is very high (e.g., > 0.85)
            # This is hardcoded since the user's threshold configures the PERCENTAGE of those matches
            FRAME_SIMILARITY_THRESHOLD = 0.85

            matched_frames = 0
            # For each frame in the shorter video (to be safe), does it exist in the longer video?
            # We want to use the first video to find matches in the second
            for f1 in frames1:
                frame_matched = False
                for f2 in frames2:
                    sim = cv2.compareHist(f1, f2, cv2.HISTCMP_CORREL)
                    if sim >= FRAME_SIMILARITY_THRESHOLD:
                        frame_matched = True
                        break # Found a match for this frame, stop checking
                
                if frame_matched:
                    matched_frames += 1

            # Determine percentage based on the minimum frames between the two
            # to handle if one video is slightly shorter
            min_frames = min(num_frames1, num_frames2)
            match_percentage = matched_frames / min_frames

            # Threshold should be out of 1.0
            threshold = float(opts.get('compare_video_accurate_threshold', 1.0)) if opts else 1.0
            
            # Since user asked for "percentage", the slider might be 0.0-1.0 or 0-100?
            # Wait, the default threshold UI creates a 0.0-1.0 spinbox for the metadata.
            # So 1.0 means 100%.
            
            return match_percentage >= threshold

        except Exception as e:
            logger.error(f"Error comparing accurate video hashes: {e}")
            return False
