import logging
from pathlib import Path
from models import FileNode, FolderNode

logger = logging.getLogger(__name__)

def build_folder_structure(root_path):
    """
    Recursively builds a tree of FileNode and FolderNode objects.
    """
    path_obj = Path(root_path)
    logger.debug(f"Building structure for directory: {path_obj}")
    if not path_obj.is_dir():
        logger.warning(f"Path is not a directory, cannot build structure: {path_obj}")
        return []

    content = []
    try:
        for item in sorted(path_obj.iterdir()):
            try:
                if item.is_dir():
                    folder_node = FolderNode(item)
                    folder_node.content = build_folder_structure(item)
                    content.append(folder_node)
                elif item.is_file():
                    file_node = FileNode(item)
                    content.append(file_node)
            except OSError as e:
                logger.error(f"Cannot access item {item} in {path_obj}: {e}")
    except OSError as e:
        logger.error(f"Cannot iterate directory {path_obj}: {e}")
    return content
