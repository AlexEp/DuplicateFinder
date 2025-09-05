from .size_calculator import SizeCalculator
from .date_calculator import DateCalculator
from .md5_calculator import MD5Calculator
from .histogram_calculator import HistogramCalculator
from .llm_embedding_calculator import LLMEmbeddingCalculator


def get_calculators(llm_engine=None, progress_callback=None):
    """
    Returns a list of all available metadata calculator instances.
    """
    calculators = [
        SizeCalculator(),
        DateCalculator(),
        MD5Calculator(),
        HistogramCalculator(),
    ]
    if llm_engine:
        llm_calculator = LLMEmbeddingCalculator(llm_engine, progress_callback)
        calculators.append(llm_calculator)
    
    return calculators
