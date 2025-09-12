import numpy as np

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Computes the cosine similarity between two vectors and scales it to a percentage.
    """
    if vec1 is None or vec2 is None:
        return 0.0

    # Normalize the vectors to unit length
    vec1_norm = vec1 / np.linalg.norm(vec1)
    vec2_norm = vec2 / np.linalg.norm(vec2)

    # Compute the dot product, which is equivalent to cosine similarity for unit vectors
    similarity = np.dot(vec1_norm, vec2_norm)

    # Convert similarity from [-1, 1] range to [0, 100] percentage
    percentage = ((similarity + 1) / 2) * 100
    
    return percentage
