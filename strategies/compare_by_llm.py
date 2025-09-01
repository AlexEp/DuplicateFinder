import numpy as np
from ai_engine.similarity import calculate_cosine_similarity

def compare(file1_metadata, file2_metadata, threshold=95.0):
    """
    Compares two files based on their pre-calculated LLM embeddings.
    """
    embedding1_list = file1_metadata.get('metadata', {}).get('llm_embedding')
    embedding2_list = file2_metadata.get('metadata', {}).get('llm_embedding')

    if embedding1_list is None or embedding2_list is None:
        return False, "N/A (missing embedding)"

    # Convert lists back to numpy arrays
    embedding1 = np.array(embedding1_list, dtype=np.float32)
    embedding2 = np.array(embedding2_list, dtype=np.float32)

    similarity_percent = calculate_cosine_similarity(embedding1, embedding2)

    # The threshold from the UI for histograms is 0-1, but for LLM let's assume 0-100.
    # The UI doesn't have a specific threshold for LLM yet. I'll assume the histogram threshold is reused for now.
    # The spec says the function should return a percentage, so the comparison logic should be in the strategy.
    # Let's check the histogram strategy. It gets a threshold. I'll do the same.

    is_similar = similarity_percent >= threshold
    
    return is_similar, f"{similarity_percent:.1f}%"
