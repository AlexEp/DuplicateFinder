from .base_calculator import BaseCalculator
import logging

logger = logging.getLogger(__name__)

class LLMEmbeddingCalculator(BaseCalculator):
    def __init__(self, llm_engine, progress_callback=None):
        self.llm_engine = llm_engine
        self.progress_callback = progress_callback
        self.processed_llm_files = 0
        self.total_llm_files = 0

    def calculate(self, file_node, opts):
        if opts.get('compare_llm') and self.llm_engine:
            if 'llm_embedding' not in file_node.metadata or file_node.metadata['llm_embedding'] is None:
                self.processed_llm_files += 1
                if self.progress_callback:
                    progress_message = f"LLM Processing ({self.processed_llm_files}/{self.total_llm_files}): {file_node.name}"
                    self.progress_callback(progress_message, self.processed_llm_files)

                embedding = self.llm_engine.get_image_embedding(str(file_node.fullpath))
                if embedding is not None:
                    file_node.metadata['llm_embedding'] = embedding.tolist()
            else:
                logger.debug(f"Using cached LLM embedding for: {file_node.fullpath}")
                self.processed_llm_files += 1
                if self.progress_callback:
                    self.progress_callback(f"LLM Cached ({self.processed_llm_files}/{self.total_llm_files}): {file_node.name}", self.processed_llm_files)
