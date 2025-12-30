from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class StrategyMetadata:
    """Metadata for UI generation."""
    option_key: str
    display_name: str
    description: str
    tooltip: str
    requires_calculation: bool = True
    has_threshold: bool = False
    threshold_label: Optional[str] = None
    default_threshold: Optional[float] = None

class BaseComparisonStrategy(ABC):
    """
    Abstract base class for all comparison strategies.
    """
    @property
    @abstractmethod
    def metadata(self) -> StrategyMetadata:
        """Strategy metadata for UI generation."""
        pass

    @property
    @abstractmethod
    def option_key(self):
        """The key in the options dictionary that enables this strategy."""
        pass

    @abstractmethod
    def compare(self, file1_info, file2_info, opts=None):
        """
        Compares two files based on a specific criterion.

        Args:
            file1_info (dict): The metadata dictionary for the first file.
            file2_info (dict): The metadata dictionary for the second file.
            opts (dict, optional): The options dictionary. Defaults to None.

        Returns:
            bool: True if the files are considered a match, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def db_key(self):
        """The key for the database column."""
        pass

    
