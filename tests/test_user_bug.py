import unittest
import os
import shutil
import sys
import tkinter as tk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from tests.headless_controller import HeadlessAppController
from database import get_db_connection, create_tables

class TestUserBug(unittest.TestCase):
    def setUp(self):
        import unittest.mock
        self.test_dir = "test_project"
        os.makedirs(self.test_dir, exist_ok=True)
        self.project_file = os.path.join(self.test_dir, "test_project.cfp-db")
        self.view = unittest.mock.Mock()
        self.controller = HeadlessAppController(self.view)
        self.controller.project_manager.create_new_project_file(self.project_file, [])

    def tearDown(self):
        self.controller.close()
        shutil.rmtree(self.test_dir)

    def test_user_bug(self):
        # Configure the view mock
        self.view.build_buttons = []
        self.view.folder_list_box.get.return_value = ["tests/imgs"]
        self.view.results_tree.get_children.return_value = []
        self.view.progress_bar = {}

        # Add the test images folder to the project
        self.controller.project_manager.add_folder("tests/imgs")

        # Set the options
        self.controller.compare_histogram.set(True)
        self.controller.histogram_method.set("Correlation")

        # Build the metadata
        self.controller.build_folders()

if __name__ == '__main__':
    unittest.main()
