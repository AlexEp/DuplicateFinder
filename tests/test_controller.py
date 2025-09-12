import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk

class TestAppController(unittest.TestCase):

    @patch('tkinter.BooleanVar')
    @patch('tkinter.StringVar')
    def setUp(self, mock_string_var, mock_boolean_var):
        self.mock_view = MagicMock()
        from controller import AppController
        self.controller = AppController(self.mock_view)
        self.controller.project_manager = MagicMock()
        self.controller.task_runner = MagicMock()

    def test_initialization(self):
        """Test that the controller initializes correctly."""
        self.mock_view.setup_ui.assert_called_once()
        self.assertEqual(self.mock_view.controller, self.controller)

    def test_clear_all_settings(self):
        """Test that all settings are cleared."""
        # We need to create specific mock instances for each variable
        # to avoid conflicts between them.
        self.controller.compare_date = MagicMock()

        self.controller.compare_date.set(True)
        self.controller.folder_structures = {1: [MagicMock()]}

        self.mock_view.results_tree.get_children.return_value = ['item1', 'item2']

        self.controller.clear_all_settings()

        self.controller.compare_date.set.assert_called_with(False)
        self.assertEqual(self.controller.folder_structures, {})

        self.mock_view.results_tree.delete.assert_any_call('item1')
        self.mock_view.results_tree.delete.assert_any_call('item2')

    @patch('controller.messagebox')
    @patch('controller.utils')
    @patch('logic.run_comparison')
    @patch('strategies.find_duplicates_strategy.run')
    def test_run_action_compare_mode(self, mock_find_duplicates_strategy_run, mock_run_comparison, mock_utils, mock_messagebox):
        """Test the main action in 'compare' mode."""
        self.controller.project_manager.current_project_path = "test.cfp-db"
        self.mock_view.folder_list_box.get.return_value = ["/folder1", "/folder2"]
        self.controller.project_manager._gather_settings.return_value = {'options': {'compare_llm': False}}
        mock_utils.calculate_metadata_db.return_value = ({}, 0)
        mock_run_comparison.return_value = [[{'name': 'file1.txt', 'size': 100, 'relative_path': 'file1.txt', 'folder_index': 1}]]
        mock_find_duplicates_strategy_run.return_value = [[{'id': 1, 'name': 'dup1.txt', 'size': 100, 'relative_path': 'path1', 'folder_index': 1}, {'id': 2, 'name': 'dup2.txt', 'size': 100, 'relative_path': 'path2', 'folder_index': 1}]]

        self.controller.run_action()

        self.controller.task_runner.run_task.assert_called_once()
        run_task_args = self.controller.task_runner.run_task.call_args
        action_task = run_task_args.args[0]
        on_success = run_task_args.args[1]

        results = action_task()
        on_success(results)

        self.assertEqual(mock_run_comparison.call_count, 1)
        self.mock_view.results_tree.insert.assert_any_call('', tk.END, values=("Comparing 'folder1' vs 'folder2' (1 match groups)", '', '', ''), open=True, tags=('header_row',))

    @patch('controller.messagebox')
    def test_calculator_integration(self, mock_messagebox):
        """
        Integration test for the calculator logic.
        This test does not mock utils.calculate_metadata_db.
        """
        import tempfile
        import os
        import sqlite3
        from controller import AppController

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
                f.write("hello")
            with open(os.path.join(tmpdir, "file2.txt"), "w") as f:
                f.write("world")

            # Set up the controller
            self.controller.project_manager.current_project_path = os.path.join(tmpdir, "test.cfp-db")
            self.mock_view.folder_list_box.get.return_value = [tmpdir]
            opts = {
                'compare_size': True,
                'compare_date': True,
                'compare_content_md5': True
            }
            self.controller.project_manager._gather_settings.return_value = opts

            # Run the build process to populate the database
            conn = sqlite3.connect(self.controller.project_manager.current_project_path)
            from database import create_tables
            create_tables(conn)
            from logic import build_folder_structure_db
            build_folder_structure_db(conn, 1, tmpdir)

            # Run the action to trigger the calculators
            self.controller._run_action_db(opts, [tmpdir])

            # Check the database to see if the metadata was calculated
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM file_metadata")
            metadata_rows = cursor.fetchall()
            cursor.execute("SELECT * FROM files")
            files_rows = cursor.fetchall()
            conn.close()

            self.assertEqual(len(metadata_rows), 2, f"files: {files_rows}, metadata: {metadata_rows}")

            self.assertEqual(len(metadata_rows), 2, f"files: {files_rows}, metadata: {metadata_rows}")

            # Find the rows for file1.txt and file2.txt
            file1_id = [r[0] for r in files_rows if r[3] == 'file1.txt'][0]
            file2_id = [r[0] for r in files_rows if r[3] == 'file2.txt'][0]

            file1_meta = [r for r in metadata_rows if r[1] == file1_id][0]
            file2_meta = [r for r in metadata_rows if r[1] == file2_id][0]

            # Check file1.txt
            self.assertEqual(file1_meta[2], 5) # size
            self.assertIsNotNone(file1_meta[3]) # date
            self.assertEqual(file1_meta[4], '5d41402abc4b2a76b9719d911017c592') # md5
            # Check file2.txt
            self.assertEqual(file2_meta[2], 5) # size
            self.assertIsNotNone(file2_meta[3]) # date
            self.assertEqual(file2_meta[4], '7d793037a0760186574b0282f2f435e7') # md5

if __name__ == '__main__':
    unittest.main()
