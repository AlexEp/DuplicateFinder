import logging
from pathlib import Path
from models import FileNode, FolderNode

logger = logging.getLogger(__name__)

def build_folder_structure(root_path):
    """
    Recursively builds a tree of FileNode and FolderNode objects.
    Returns a tuple containing the content list and a list of inaccessible paths.
    """
    path_obj = Path(root_path)
    logger.debug(f"Building structure for directory: {path_obj}")
    if not path_obj.is_dir():
        logger.warning(f"Path is not a directory, cannot build structure: {path_obj}")
        return [], [str(path_obj)]

    content = []
    inaccessible_paths = []
    try:
        for item in sorted(path_obj.iterdir()):
            try:
                if item.is_dir():
                    folder_node = FolderNode(item)
                    folder_node.content, new_inaccessible = build_folder_structure(item)
                    content.append(folder_node)
                    inaccessible_paths.extend(new_inaccessible)
                elif item.is_file():
                    # This check is basic, a more thorough check would be to try and open the file
                    # but for now, just checking if it's a file is enough.
                    file_node = FileNode(item)
                    content.append(file_node)
            except OSError as e:
                logger.error(f"Cannot access item {item} in {path_obj}: {e}")
                inaccessible_paths.append(str(item))
    except OSError as e:
        logger.error(f"Cannot iterate directory {path_obj}: {e}")
        inaccessible_paths.append(str(path_obj))
    return content, inaccessible_paths
