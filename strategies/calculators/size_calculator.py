from .base_calculator import BaseCalculator
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SizeCalculator(BaseCalculator):
    def calculate(self, file_node, opts):
        if opts.get('compare_size'):
            if 'size' not in file_node.metadata or file_node.metadata['size'] is None:
                try:
                    p = Path(file_node.fullpath)
                    stat = p.stat()
                    file_node.metadata['size'] = stat.st_size
                except OSError as e:
                    logger.error(f"Could not get stat for file {file_node.fullpath}: {e}")
