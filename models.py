class FileSystemNode:
    """Base class for nodes in the file system tree."""
    def __init__(self, path_obj):
        self.name = path_obj.name
        self.fullpath = str(path_obj.resolve())

    def to_dict(self):
        """Converts the node to a dictionary (for JSON serialization)."""
        raise NotImplementedError("Subclasses must implement this method.")

class FileNode(FileSystemNode):
    """Represents a file in the file system tree."""
    def __init__(self, path_obj, metadata=None):
        super().__init__(path_obj)
        self.path_obj = path_obj
        self.type = 'file'
        self.metadata = metadata if metadata is not None else {}

    @property
    def ext(self):
        return "".join(self.path_obj.suffixes)

    def to_dict(self):
        return {
            'type': self.type,
            'name': self.name,
            'fullpath': self.fullpath,
            'metadata': self.metadata
        }

class FolderNode(FileSystemNode):
    """Represents a folder in the file system tree."""
    def __init__(self, path_obj):
        super().__init__(path_obj)
        self.type = 'folder'
        self.content = []  # List of FileNode and FolderNode objects

    def to_dict(self):
        return {
            'type': self.type,
            'name': self.name,
            'fullpath': self.fullpath,
            'content': [node.to_dict() for node in self.content]
        }
