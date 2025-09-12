import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import numpy as np
from config import config

# Conditionally import LLM-related modules
use_llm = config.get('use_llm', False)
if use_llm:
    from strategies import compare_by_llm
    # We avoid importing the real engine here to prevent it from loading
    # The 'ai_engine.engine.LlavaEmbeddingEngine' string will be used for mocking

# Define test cases directly in the file
# Structure: ( (image1_basename, image2_basename), expected_result, description )
# expected_result: 'similar', 'dissimilar', or a tuple (min_score, max_score) for nuanced cases
TEST_CASES = [
    (("1122", "5566"), "similar", "Same image, different colors"),
    (("1320", "7766"), "similar", "Same image, different size and format (avif vs webp)"),
    (("9988", "9900"), "dissimilar", "Completely different images"),
    (("2358", "8151"), "dissimilar", "Completely different images 2"),
    (("1623", "9574"), (70.0, 95.0), "Similar theme (car), but not the same image"),
    (("4815", "6234"), (70.0, 95.0), "Similar theme (person), but not the same image"),
]

# Create fake embeddings for each test image
# In a real scenario, these would be pre-computed or representative vectors
FAKE_EMBEDDINGS = {
    # Group 1: Identical images (different colors) -> high similarity
    "1122": np.array([0.1, 0.9, 0.2, 0.8]),
    "5566": np.array([0.1, 0.9, 0.2, 0.8]),
    # Group 2: Identical images (different size/format) -> high similarity
    "1320": np.array([0.5, 0.5, 0.5, 0.5]),
    "7766": np.array([0.5, 0.5, 0.5, 0.5]),
    # Group 3: Dissimilar images -> low similarity
    "9988": np.array([1.0, 0.0, 0.0, 0.0]),
    "9900": np.array([0.0, 0.0, 1.0, 0.0]),
    # Group 4: Dissimilar images 2 -> low similarity
    "2358": np.array([0.0, 1.0, 0.0, 0.0]),
    "8151": np.array([0.0, 0.0, 0.0, 1.0]),
    # Group 5: Similar but not same (cars) -> medium-high similarity
    "1623": np.array([0.8, 0.2, 0.6, 0.4]),
    "9574": np.array([0.7, 0.3, 0.5, 0.5]), # Slightly different vector
    # Group 6: Similar but not same (people) -> medium-high similarity
    "4815": np.array([0.2, 0.6, 0.8, 0.1]),
    "6234": np.array([0.3, 0.5, 0.7, 0.2]), # Slightly different vector
}

@unittest.skipIf(not use_llm, "LLM tests are disabled in settings.json")
class TestLLMSimilarity(unittest.TestCase):

    @patch('ai_engine.engine.LlavaEmbeddingEngine')
    def test_image_similarity(self, MockLlavaEngine):
        """
        Tests image similarity using a mocked LLM engine and self-contained test cases.
        """
        # Configure the mock engine instance
        mock_engine_instance = MockLlavaEngine.return_value

        def get_embedding_side_effect(image_path):
            """
            Return the fake embedding based on the image's base name.
            This simulates the behavior of the real engine.
            """
            base_name = Path(image_path).stem
            embedding = FAKE_EMBEDDINGS.get(base_name)
            if embedding is None:
                self.fail(f"Test setup error: No fake embedding found for image '{base_name}'")
            return embedding

        mock_engine_instance.get_image_embedding.side_effect = get_embedding_side_effect

        # This object is now a mock, but we can still "initialize" it
        # The patch decorator ensures the real one is never touched
        llm_engine = MockLlavaEngine()

        for (image1_base, image2_base), expectation, description in TEST_CASES:
            with self.subTest(msg=description):
                # We use dummy paths because the mock intercepts the call anyway
                path1 = f"tests/imgs/{image1_base}.jpg"
                path2 = f"tests/imgs/{image2_base}.jpg"

                # Get embeddings from the mocked engine
                embedding1 = llm_engine.get_image_embedding(path1)
                embedding2 = llm_engine.get_image_embedding(path2)

                # Prepare metadata dicts for the compare function
                file1_info = {'metadata': {'llm_embedding': embedding1.tolist()}}
                file2_info = {'metadata': {'llm_embedding': embedding2.tolist()}}

                # Call the comparison function
                is_similar, score_str = compare_by_llm.compare(
                    file1_info,
                    file2_info,
                    threshold=95.0 # High threshold for "identical" cases
                )

                # Extract the numeric score for range-based assertions
                try:
                    score = float(score_str.replace('%', ''))
                except (ValueError, AttributeError):
                    self.fail(f"Could not parse score from '{score_str}'")

                if expectation == 'similar':
                    self.assertTrue(is_similar, f"Expected images to be similar: {description}")
                    self.assertGreaterEqual(score, 95.0)
                elif expectation == 'dissimilar':
                    self.assertFalse(is_similar, f"Expected images to be dissimilar: {description}")
                    self.assertLess(score, 95.0)
                elif isinstance(expectation, tuple):
                    min_score, max_score = expectation
                    self.assertTrue(min_score <= score <= max_score,
                                    f"Score {score:.1f}% for '{description}' was not in the expected range [{min_score}, {max_score}]")

                    # Test threshold boundaries
                    is_similar_low_thresh, _ = compare_by_llm.compare(file1_info, file2_info, threshold=min_score - 1)
                    self.assertTrue(is_similar_low_thresh, f"Should be similar with threshold below min_score for '{description}'")

                    is_similar_high_thresh, _ = compare_by_llm.compare(file1_info, file2_info, threshold=max_score + 1)
                    self.assertFalse(is_similar_high_thresh, f"Should be dissimilar with threshold above max_score for '{description}'")

if __name__ == '__main__':
    unittest.main()
