import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any
from interfaces.service_interface import IFileService

logger = logging.getLogger(__name__)

class FileService(IFileService):
    """Concrete implementation of IFileService."""
    
    def scan_folder(self, path: Path, include_subfolders: bool = True) -> List[Dict[str, Any]]:
        """
        Scans a folder and returns a list of file info dicts.
        This is a wrapper around filesystem calls, not database.
        """
        files = []
        iterator = path.rglob('*') if include_subfolders else path.glob('*')
        for item in iterator:
            if item.is_file():
                try:
                    stats = item.stat()
                    files.append({
                        'path': item.parent,
                        'name': item.name,
                        'ext': item.suffix.lower(),
                        'size': stats.st_size,
                        'modified_date': stats.st_mtime
                    })
                except OSError as e:
                    logger.error(f"Error accessing {item}: {e}")
        return files

    def delete_file(self, path: Path) -> bool:
        """Deletes a file from the filesystem."""
        try:
            if path.is_file():
                os.remove(path)
                logger.info(f"Deleted file: {path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False

    def move_file(self, source: Path, destination: Path) -> bool:
        """Moves a file from source to destination."""
        try:
            if not source.is_file():
                logger.error(f"Move failed: source file does not exist at {source}")
                return False
            
            # Ensure destination parent exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(source, destination)
            logger.info(f"Moved file from {source} to {destination}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file from {source} to {destination}: {e}")
            return False

    def open_folder(self, path: Path) -> bool:
        """Opens the folder in the system file explorer."""
        import sys
        import subprocess
        try:
            if not path.is_dir():
                path = path.parent
            
            if not path.is_dir():
                logger.error(f"Cannot open folder: {path} is not a directory.")
                return False

            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return True
        except Exception as e:
            logger.error(f"Failed to open folder {path}: {e}")
            return False
