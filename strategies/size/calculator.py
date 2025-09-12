from ..base_calculator import BaseCalculator
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SizeCalculator(BaseCalculator):
    @property
    def db_key(self):
        return 'size'

    def calculate(self, file_node, opts):
        """
        Calculates the size of a file.

        Args:
            file_node (FileNode): The file node to process.
            opts (dict): The options dictionary.

        Returns:
            int: The size of the file in bytes, or None if an error occurs.
        """
        if opts.get('compare_size'):
            if 'size' not in file_node.metadata or file_node.metadata['size'] is None:
                try:
                    p = Path(file_node.fullpath)
                    stat = p.stat()
                    return stat.st_size
                except OSError as e:
                    logger.error(f"Could not get stat for file {file_node.fullpath}: {e}")
                    return None
        return None
