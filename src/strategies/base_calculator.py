from abc import ABC, abstractmethod
import os
import logging
from services.cache_manager import MetricCache

logger = logging.getLogger(__name__)

class BaseCalculator(ABC):
    """
    Abstract base class for metadata calculators.
    """
    def calculate(self, file_node, opts):
        """
        Calculates a specific piece of metadata for a given file node,
        utilizing caching if available.
        """
        # Determine file size to use as part of the cache key
        file_size = file_node.metadata.get('size')
        if file_size is None:
            try:
                file_size = os.path.getsize(file_node.fullpath)
            except OSError as e:
                logger.error(f"Could not get file size for cache key {file_node.fullpath}: {e}")
                file_size = 0 # Fallback 

        cache = MetricCache()
        
        # 1. Clean old entries periodically (every time is fine since it's fast with an index/timestamp, 
        # but could be optimized if it becomes a bottleneck)
        cache.clean_old_cache(30)

        # 2. Check cache
        cached_value = cache.get_metric(file_node.fullpath, file_size, self.db_key)
        if cached_value is not None:
            return cached_value

        # 3. Calculate if not in cache
        result = self._calculate(file_node, opts)

        # 4. Save to cache
        if result is not None:
             cache.set_metric(file_node.fullpath, file_size, self.db_key, result)

        return result

    @abstractmethod
    def _calculate(self, file_node, opts):
        """
        The actual calculation logic to be implemented by subclasses.
        """
        pass

    @property
    @abstractmethod
    def db_key(self):
        """The key for the database column."""
        pass
