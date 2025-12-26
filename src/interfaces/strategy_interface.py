from abc import ABC, abstractmethod

class IComparisonStrategy(ABC):
    """Interface for file comparison algorithms."""
    
    @property
    @abstractmethod
    def option_key(self) -> str:
        """The key in options dictionary that enables this strategy."""
        pass

    @abstractmethod
    def compare(self, file1_info: dict, file2_info: dict, opts: dict = None) -> bool:
        """Compare two files."""
        pass

class IMetadataCalculator(ABC):
    """Interface for file metadata calculators."""
    
    @abstractmethod
    def calculate(self, file_node, opts: dict):
        """Calculate a specific metadata (e.g., MD5)."""
        pass
