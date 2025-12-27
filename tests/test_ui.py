import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
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
        self.app.include_subfolders = MagicMock()
        self.app.compare_name = MagicMock()
        self.app.compare_date = MagicMock()
        self.app.compare_size = MagicMock()
        self.app.compare_content_md5 = MagicMock()
        self.app.compare_histogram = MagicMock()
        self.app.histogram_method = MagicMock()
        self.app.histogram_threshold = MagicMock()
        self.app.compare_llm = MagicMock()
        self.app.llm_similarity_threshold = MagicMock()
        self.app.move_to_path = MagicMock()

    def test_initialization(self):
        """Test that the UI initializes correctly with components."""
        self.assertEqual(self.app.root, self.root)
        self.assertIsNotNone(self.app.controller)
        
        # Check that components are created
        self.app.create_widgets()
        self.assertIsNotNone(self.app._status_bar)
        self.assertIsNotNone(self.app._settings_panel)
        self.assertIsNotNone(self.app._folder_selection)
        self.assertIsNotNone(self.app._results_view)

    def test_update_status(self):
        """Test the update_status method delegates to StatusBar."""
        self.app.create_widgets()
        self.app._status_bar = MagicMock()
        
        self.app.update_status("Test Message", 50)
        self.app._status_bar.set_message.assert_called_with("Test Message")
        self.app._status_bar.set_progress.assert_called_with(50)

if __name__ == '__main__':
    unittest.main()
