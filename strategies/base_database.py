from abc import ABC, abstractmethod

class BaseDatabase(ABC):
    """
    Abstract base class for database operations for a strategy.
    """
    @abstractmethod
    def save(self, conn, file_id, data):
        """
        Saves data for a specific file to the database.

        Args:
            conn: The database connection.
            file_id (int): The ID of the file.
            data: The data to save.
        """
        pass

    @abstractmethod
    def load(self, conn, file_id):
        """
        Loads data for a specific file from the database.

        Args:
            conn: The database connection.
            file_id (int): The ID of the file.

        Returns:
            The loaded data.
        """
        pass
