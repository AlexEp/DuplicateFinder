from ..base_calculator import BaseCalculator
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DateCalculator(BaseCalculator):
    def calculate(self, file_node, opts):
        """
        Calculates the modification date of a file.

        Args:
            file_node (FileNode): The file node to process.
            opts (dict): The options dictionary.

        Returns:
            float: The modification time of the file, or None if an error occurs.
        """
        if opts.get('compare_date'):
            if 'date' not in file_node.metadata or file_node.metadata['date'] is None:
                try:
                    p = Path(file_node.fullpath)
                    stat = p.stat()
                    return stat.st_mtime
                except OSError as e:
                    logger.error(f"Could not get stat for file {file_node.fullpath}: {e}")
                    return None
        return None
