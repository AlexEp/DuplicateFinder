import numpy as np
from ai_engine.similarity import calculate_cosine_similarity
import constants

def compare(file1_info, file2_info, threshold):
    """
    Compares two files based on their pre-calculated LLM embeddings.
    The threshold is a float between 0.0 and 1.0.
    """
    embedding1_bytes = file1_info.get(constants.METADATA_LLM_EMBEDDING)
    embedding2_bytes = file2_info.get(constants.METADATA_LLM_EMBEDDING)

    if embedding1_bytes is None or embedding2_bytes is None:
        return False, 0.0

    # Convert bytes back to numpy arrays
    embedding1 = np.frombuffer(embedding1_bytes, dtype=np.float32)
    embedding2 = np.frombuffer(embedding2_bytes, dtype=np.float32)

    # This returns a value from 0-100
    similarity_percent = calculate_cosine_similarity(embedding1, embedding2)

    # Convert to a 0.0-1.0 scale to match the threshold
    similarity_score = similarity_percent / 100.0

    return similarity_score >= threshold, similarity_score