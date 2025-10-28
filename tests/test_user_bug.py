import unittest
import os
import shutil
import sys
import tkinter as tk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tests.headless_controller import HeadlessAppController
from src.database import get_db_connection, create_tables

class TestUserBug(unittest.TestCase):
    def setUp(self):
        import unittest.mock
        self.test_dir = "test_project"
        os.makedirs(self.test_dir, exist_ok=True)
        self.project_file = os.path.join(self.test_dir, "test_project.cfp-db")
        self.view = unittest.mock.Mock()
        self.controller = HeadlessAppController(self.view)
        self.controller.project_manager.create_new_project_file(self.project_file, ["tests/imgs"])

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_user_bug(self):
        from src.strategies.strategy_registry import _STRATEGIES
        histogram_strategies = [key for key in _STRATEGIES.keys() if key.startswith('compare_histogram_')]

        for strategy_key in histogram_strategies:
            with self.subTest(strategy=strategy_key):
                # Configure the view mock
                self.view.build_buttons = []
                self.view.folder_list_box.get.return_value = ["tests/imgs"]

                # Set the options
                # First, reset all comparison options
                for key in _STRATEGIES.keys():
                    if hasattr(self.controller, key):
                        mock = unittest.mock.MagicMock()
                        mock.get.return_value = False
                        setattr(self.controller, key, mock)

                # Enable the current histogram strategy
                mock = unittest.mock.MagicMock()
                mock.get.return_value = True
                setattr(self.controller, strategy_key, mock)

                # Build the metadata
                self.controller.build_folders()

                # Run the action and get the results
                results = self.controller._run_action_db(self.controller.project_manager._gather_settings(), ["tests/imgs"])

                # Assert that duplicates were found
                self.assertGreater(len(results), 0, f"No duplicates found for strategy {strategy_key}")

if __name__ == '__main__':
    unittest.main()
