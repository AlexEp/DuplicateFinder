import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
from ui import FolderComparisonApp

class TestFolderComparisonApp(unittest.TestCase):

    @patch('tkinter.BooleanVar')
    @patch('tkinter.StringVar')
    def setUp(self, mock_string_var, mock_boolean_var):
        self.root = MagicMock()
        self.app = FolderComparisonApp(self.root)
        self.app.controller = MagicMock()

        # Mock the variables that are created in the controller
        self.app.file_type_filter = MagicMock()
        self.app.compare_content_md5 = MagicMock()
        self.app.compare_histogram = MagicMock()
        self.app.histogram_method = MagicMock()

    def test_initialization(self):
        """Test that the UI initializes correctly."""
        self.assertEqual(self.app.root, self.root)
        self.assertIsNotNone(self.app.controller)

    def test_on_file_type_change(self):
        """Test the _on_file_type_change method."""
        # Mock the frame
        self.app.image_match_frame = MagicMock()
        self.app.compare_histogram = MagicMock()
        self.app.compare_llm = MagicMock()

        # Test "image" file type
        self.app.file_type_filter.get.return_value = "image"
        self.app._on_file_type_change()
        self.app.image_match_frame.pack.assert_called_once_with(fill=tk.X, pady=(5,0))

        # Test other file type
        self.app.file_type_filter.get.return_value = "video"
        self.app._on_file_type_change()
        self.app.image_match_frame.pack_forget.assert_called_once()
        self.app.compare_histogram.set.assert_called_with(False)
        self.app.compare_llm.set.assert_called_with(False)

if __name__ == '__main__':
    unittest.main()
