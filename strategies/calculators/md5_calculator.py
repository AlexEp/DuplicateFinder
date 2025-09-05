from .base_calculator import BaseCalculator
from .. import utils
import logging

logger = logging.getLogger(__name__)

class MD5Calculator(BaseCalculator):
    def calculate(self, file_node, opts):
        if opts.get('compare_content_md5'):
            file_node.metadata['md5'] = utils.calculate_md5(file_node.fullpath)
