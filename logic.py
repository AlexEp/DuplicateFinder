from pathlib import Path
from models import FileNode, FolderNode

def build_folder_structure(root_path):
    """
    Recursively builds a tree of FileNode and FolderNode objects.
    """
    path_obj = Path(root_path)
    if not path_obj.is_dir():
        return []

    content = []
    for item in sorted(path_obj.iterdir()):
        if item.is_dir():
            folder_node = FolderNode(item)
            folder_node.content = build_folder_structure(item)
            content.append(folder_node)
        elif item.is_file():
            file_node = FileNode(item)
            content.append(file_node)
    return content
