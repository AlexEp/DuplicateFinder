from abc import ABC, abstractmethod

class BaseComparisonStrategy(ABC):
    """
    Abstract base class for all comparison strategies.
    """
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

    @abstractmethod
    def get_duplications_ids(self, conn, folder_index=None):
        """
        Finds duplicate files based on the strategy's criterion.

        Args:
            conn: The database connection.
            folder_index (int, optional): The index of the folder to search in.
                                        If None, search in all folders. Defaults to None.

        Returns:
            list[list[int]]: A list of lists, where each inner list contains the file IDs of a group of duplicate files.
        """
        pass
