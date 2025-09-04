from .base_comparison_strategy import BaseComparisonStrategy
import numpy as np
from ai_engine.similarity import calculate_cosine_similarity

class CompareByLLM(BaseComparisonStrategy):
    @property
    def option_key(self):
        return 'compare_llm'

    def compare(self, file1_info, file2_info, opts=None):
        """
        Compares two files based on their pre-calculated LLM embeddings.
        The threshold is a float between 0.0 and 1.0.
        """
        if opts is None: opts = {}
        threshold = float(opts.get('llm_similarity_threshold', 0.8))

        embedding1_bytes = file1_info.get('llm_embedding')
        embedding2_bytes = file2_info.get('llm_embedding')

        if embedding1_bytes is None or embedding2_bytes is None:
            return False

        # Convert bytes back to numpy arrays
        embedding1 = np.frombuffer(embedding1_bytes, dtype=np.float32)
        embedding2 = np.frombuffer(embedding2_bytes, dtype=np.float32)

        # This returns a value from 0-100
        similarity_percent = calculate_cosine_similarity(embedding1, embedding2)

        # Convert to a 0.0-1.0 scale to match the threshold
        similarity_score = similarity_percent / 100.0

        return similarity_score >= threshold