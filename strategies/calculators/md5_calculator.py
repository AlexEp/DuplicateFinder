from .base_calculator import BaseCalculator
from .. import utils
import logging

logger = logging.getLogger(__name__)

class MD5Calculator(BaseCalculator):
    def calculate(self, file_node, opts):
        if opts.get('compare_content_md5'):
            if 'md5' not in file_node.metadata or file_node.metadata['md5'] is None:
                file_node.metadata['md5'] = utils.calculate_md5(file_node.fullpath)
            else:
                logger.debug(f"Using cached MD5 for: {file_node.fullpath}")
