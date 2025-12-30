from ..base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata
import numpy as np

class CompareByLLM(BaseComparisonStrategy):
    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_llm',
            display_name='LLM Content (Image)',
            description='Compare images by semantic content using AI',
            tooltip='Uses a vision model to understand the content of images. Can find similar images even if they are visually different (e.g., different angles).',
            requires_calculation=True,
            has_threshold=True,
            threshold_label='LLM Threshold',
            default_threshold=0.8
        )

    @property
    def option_key(self):
        return 'compare_llm'

    def compare(self, file1_info, file2_info, opts=None):
        """
        Compares two files based on their LLM embeddings.
        """
        emb1 = file1_info.get('llm_embedding')
        emb2 = file2_info.get('llm_embedding')

        if emb1 is None or emb2 is None:
            return False

        # Convert bytes to numpy arrays
        v1 = np.frombuffer(emb1, dtype=np.float32)
        v2 = np.frombuffer(emb2, dtype=np.float32)

        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return False
            
        similarity = dot_product / (norm_v1 * norm_v2)
        
        threshold = float(opts.get('llm_similarity_threshold', 0.8))
        return similarity >= threshold

    @property
    def db_key(self):
        return 'llm_embedding'

    def get_duplicates_query_part(self):
        # LLM embeddings are too large for GROUP BY in SQLite effectively
        # So we might need a different approach for duplicates if only LLM is used.
        # For now, returning None to indicate it's a refinement strategy.
        return None
