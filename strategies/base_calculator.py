from abc import ABC, abstractmethod

class BaseCalculator(ABC):
    """
    Abstract base class for metadata calculators.
    """
    @abstractmethod
    def calculate(self, file_node, opts):
        """
        Calculates a specific piece of metadata for a given file node.

        Args:
            file_node (FileNode): The file node to process.
            opts (dict): The options dictionary.
        """
        pass

    @property
    @abstractmethod
    def db_key(self):
        """The key for the database column."""
        pass
