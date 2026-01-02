import os
from pathlib import Path
from errors import ValidationError

class PathValidator:
    """Helper class for validating file system paths."""
    
    @staticmethod
    def validate_dir(path: Path):
        """Validates that a path is an existing, readable directory."""
        if not path.exists():
            raise ValidationError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")
        if not os.access(path, os.R_OK):
            raise ValidationError(f"No read permission for directory: {path}")

    @staticmethod
    def validate_file(path: Path):
        """Validates that a path is an existing, readable file."""
        if not path.exists():
            raise ValidationError(f"File does not exist: {path}")
        if not path.is_file():
            raise ValidationError(f"Path is not a file: {path}")
        if not os.access(path, os.R_OK):
            raise ValidationError(f"No read permission for file: {path}")

class ComparisonValidator:
    """Helper class for validating comparison options and inputs."""
    
    @staticmethod
    def validate_folders(folder_indices: list):
        """Validates that at least one folder is selected for analysis."""
        if not folder_indices:
            raise ValidationError("No folders selected for analysis.")
