from pathlib import Path

class FileSystemNode:
    """Base class for nodes in the file system tree."""
    def __init__(self, path_obj, root_path=None):
        self.name = path_obj.name
        self.fullpath = str(path_obj.resolve())
        # Store relative path for portability
        if root_path:
            self.relative_path = str(Path(self.fullpath).relative_to(root_path))
        else:
            # Fallback for older project files or other contexts
            self.relative_path = self.name

    def to_dict(self):
        """Converts the node to a dictionary (for JSON serialization)."""
        raise NotImplementedError("Subclasses must implement this method.")

class FileNode(FileSystemNode):
    """Represents a file in the file system tree."""
    def __init__(self, path_obj, root_path=None, metadata=None):
        super().__init__(path_obj, root_path)
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
            'relative_path': self.relative_path,
            'metadata': self.metadata
        }
