from ..base_calculator import BaseCalculator
from .. import utils
import logging

logger = logging.getLogger(__name__)

class MD5Calculator(BaseCalculator):
    @property
    def db_key(self):
        return 'md5'

    def calculate(self, file_node, opts):
        """
        Calculates the MD5 hash of a file.

        Args:
            file_node (FileNode): The file node to process.
            opts (dict): The options dictionary.

        Returns:
            str: The MD5 hash of the file, or None if an error occurs.
        """
        if opts.get('compare_content_md5'):
            return utils.calculate_md5(file_node.fullpath)
        return None
