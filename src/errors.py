class DuplicateFinderError(Exception):
    """Base exception for the DuplicateFinder application."""
    pass

class RepositoryError(DuplicateFinderError):
    """Exception raised for errors related to data repositories."""
    pass

class StrategyError(DuplicateFinderError):
    """Exception raised for errors during execution of comparison strategies."""
    pass

class ValidationError(DuplicateFinderError):
    """Exception raised for input validation errors."""
    pass

class FileOperationError(DuplicateFinderError):
    """Exception raised for errors during file system operations."""
    pass
