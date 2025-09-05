from .base_calculator import BaseCalculator
from .. import compare_by_histogram
import logging

logger = logging.getLogger(__name__)

class HistogramCalculator(BaseCalculator):
    def calculate(self, file_node, opts):
        if opts.get('compare_histogram'):
            if 'histogram' not in file_node.metadata or file_node.metadata['histogram'] is None:
                hist = compare_by_histogram.get_histogram(str(file_node.fullpath))
                if hist is not None:
                    file_node.metadata['histogram'] = hist
            else:
                logger.debug(f"Using cached histogram for: {file_node.fullpath}")
