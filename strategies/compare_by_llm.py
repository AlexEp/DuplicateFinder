import numpy as np
from ai_engine.similarity import calculate_cosine_similarity

def compare(file1_metadata, file2_metadata, threshold=0.8):
    """
    Compares two files based on their pre-calculated LLM embeddings.
    The threshold is a float between 0.0 and 1.0.
    """
    embedding1_list = file1_metadata.get('metadata', {}).get('llm_embedding')
    embedding2_list = file2_metadata.get('metadata', {}).get('llm_embedding')

    if embedding1_list is None or embedding2_list is None:
        return False, "N/A (missing embedding)"

    # Convert lists back to numpy arrays
    embedding1 = np.array(embedding1_list, dtype=np.float32)
    embedding2 = np.array(embedding2_list, dtype=np.float32)

    # This returns a value from 0-100
    similarity_percent = calculate_cosine_similarity(embedding1, embedding2)

    # Convert to a 0.0-1.0 scale to match the threshold
    similarity_score = similarity_percent / 100.0

    is_similar = similarity_score >= threshold
    
    return is_similar, f"{similarity_score:.2f}"
