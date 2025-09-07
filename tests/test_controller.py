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
    @patch('controller.find_common_strategy')
    def test_run_action_compare_mode(self, mock_find_common, mock_utils, mock_messagebox):
        """Test the main action in 'compare' mode."""
        self.controller.project_manager.current_project_path = "test.cfp-db"
        self.mock_view.folder_list_box.get.return_value = ["/folder1", "/folder2"]
        self.controller.project_manager._gather_settings.return_value = {'options': {'compare_llm': False}}
        mock_utils.calculate_metadata_db.return_value = ({}, 0)
        mock_find_common.run.return_value = [{'name': 'file1.txt', 'size': 100, 'relative_path': 'file1.txt'}]

        self.controller.run_action()

        self.controller.task_runner.run_task.assert_called_once()
        run_task_args = self.controller.task_runner.run_task.call_args
        action_task = run_task_args.args[0]
        on_success = run_task_args.args[1]

        results = action_task()
        on_success(results)

        self.assertEqual(mock_find_common.run.call_count, 1)
        self.mock_view.results_tree.insert.assert_any_call('', tk.END, values=("Comparing 'folder1' vs 'folder2' (1 matches)", '', '', ''), open=True, tags=('header_row',))

if __name__ == '__main__':
    unittest.main()
