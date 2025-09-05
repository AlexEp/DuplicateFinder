import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import logic
from models import FileNode, FolderNode

class TestLogic(unittest.TestCase):

    def test_build_folder_structure_json(self):
        """Test building a folder structure for JSON projects."""
        # Create a mock file system structure
        # Create a mock file system structure
        mock_file1 = MagicMock(spec=Path)
        mock_file1.name = "file1.txt"
        mock_file1.is_dir.return_value = False
        mock_file1.is_file.return_value = True

        mock_subfolder = MagicMock(spec=Path)
        mock_subfolder.name = "subfolder"
        mock_subfolder.is_dir.return_value = True
        mock_subfolder.is_file.return_value = False

        mock_file2 = MagicMock(spec=Path)
        mock_file2.name = "file2.txt"
        mock_file2.is_dir.return_value = False
        mock_file2.is_file.return_value = True

        # Make the mocks comparable
        mock_file1.__lt__ = lambda self, other: self.name < other.name
        mock_subfolder.__lt__ = lambda self, other: self.name < other.name
        mock_file2.__lt__ = lambda self, other: self.name < other.name

        mock_root = MagicMock(spec=Path)
        mock_root.is_dir.return_value = True
        mock_root.iterdir.return_value = [mock_file1, mock_subfolder]

        mock_subfolder.iterdir.return_value = [mock_file2]

        # Patch Path() to return our mock objects
        with patch('logic.Path', return_value=mock_root) as mock_path:
            # When build_folder_structure is called recursively for the subfolder,
            # we need to make sure the Path constructor returns the subfolder mock.
            def path_side_effect(path_arg):
                if path_arg == mock_subfolder:
                    return mock_subfolder
                return mock_root
            mock_path.side_effect = path_side_effect

            # Call the function
            structure, inaccessible_paths = logic.build_folder_structure("dummy_path")

        # Assertions
        self.assertEqual(len(structure), 2)
        self.assertIsInstance(structure[0], FileNode)
        self.assertEqual(structure[0].name, "file1.txt")
        self.assertIsInstance(structure[1], FolderNode)
        self.assertEqual(structure[1].name, "subfolder")
        self.assertEqual(len(structure[1].content), 1)
        self.assertIsInstance(structure[1].content[0], FileNode)
        self.assertEqual(structure[1].content[0].name, "file2.txt")
        self.assertEqual(len(inaccessible_paths), 0)

    def test_build_folder_structure_db(self):
        """Test building a folder structure for SQLite projects."""
        # Mock connection and cursor
        mock_conn = MagicMock()

        # Create a mock file system structure
        mock_file1 = MagicMock(spec=Path)
        mock_file1.name = "file1.txt"
        mock_file1.suffix = ".txt"
        mock_file1.is_file.return_value = True
        mock_file1.stat.return_value.st_size = 100
        mock_file1.stat.return_value.st_mtime = 12345.0

        mock_root = MagicMock(spec=Path)
        mock_root.is_dir.return_value = True
        mock_root.rglob.return_value = [mock_file1]

        # Mock relative_to to return a mock object with an as_posix method
        relative_path_mock = MagicMock()
        relative_path_mock.as_posix.return_value = "file1.txt"
        mock_file1.relative_to.return_value = relative_path_mock

        with patch('logic.Path', return_value=mock_root):
            logic.build_folder_structure_db(mock_conn, 1, "dummy_path")

        # Assertions
        mock_conn.executemany.assert_called_once()
        args, _ = mock_conn.executemany.call_args
        self.assertIn("INSERT INTO files", args[0])
        self.assertEqual(len(args[1]), 1)
        self.assertEqual(args[1][0]['name'], 'file1.txt')

if __name__ == '__main__':
    unittest.main()
