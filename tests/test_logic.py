import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import logic
from models import FileNode

class TestLogic(unittest.TestCase):

    def test_build_folder_structure_json(self):
        """Test building a folder structure for JSON projects (new flat model)."""
        # Create a mock file system structure
        mock_file1 = MagicMock(spec=Path)
        mock_file1.name = "file1.txt"
        mock_file1.is_file.return_value = True

        mock_file2 = MagicMock(spec=Path)
        mock_file2.name = "file2.txt"
        mock_file2.is_file.return_value = True

        # is_file for directories should be false
        mock_dir = MagicMock(spec=Path)
        mock_dir.name = "subfolder"
        mock_dir.is_file.return_value = False

        mock_root_path_str = "/tmp/dummy_root"
        mock_file1_path = Path(mock_root_path_str) / "file1.txt"
        mock_file2_path = Path(mock_root_path_str) / "sub" / "file2.txt"

        mock_file1 = MagicMock(spec=Path)
        mock_file1.name = "file1.txt"
        mock_file1.is_file.return_value = True
        mock_file1.resolve.return_value = mock_file1_path

        mock_file2 = MagicMock(spec=Path)
        mock_file2.name = "file2.txt"
        mock_file2.is_file.return_value = True
        mock_file2.resolve.return_value = mock_file2_path

        mock_dir = MagicMock(spec=Path)
        mock_dir.name = "sub"
        mock_dir.is_file.return_value = False

        mock_root = MagicMock(spec=Path)
        mock_root.is_dir.return_value = True
        mock_root.rglob.return_value = [mock_file1, mock_dir, mock_file2]

        # Patch Path() to return our mock root
        with patch('logic.Path') as mock_path_constructor:
            mock_path_constructor.return_value = mock_root
            # Call the function
            structure, inaccessible_paths = logic.build_folder_structure(mock_root_path_str)

        # Assertions
        self.assertEqual(len(structure), 2)
        self.assertIsInstance(structure[0], FileNode)
        self.assertEqual(structure[0].name, "file1.txt")
        self.assertIsInstance(structure[1], FileNode)
        self.assertEqual(structure[1].name, "file2.txt")
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
