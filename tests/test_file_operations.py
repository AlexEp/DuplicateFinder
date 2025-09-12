import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import sqlite3
from pathlib import Path
import os
import shutil
import tempfile

from file_operations import delete_file, move_file
from models import FileNode, FolderNode

class TestFileOperations(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dest_dir = os.path.join(self.test_dir, "dest")
        os.makedirs(self.dest_dir)
        self.db_path = os.path.join(self.test_dir, "test.cfp-db")
        self.conn = sqlite3.connect(self.db_path)
        from database import create_tables
        create_tables(self.conn)

    def tearDown(self):
        self.conn.close()
        try:
            shutil.rmtree(self.test_dir)
        except PermissionError:
            pass

    @patch('file_operations.messagebox')
    def test_delete_file_json(self, mock_messagebox):
        mock_controller = MagicMock()
        mock_controller.project_manager.current_project_path = "test.cfp"
        mock_controller.folder1_path.get.return_value = self.test_dir
        mock_controller.folder2_path.get.return_value = ""

        file_to_delete = Path(self.test_dir) / "file1.txt"
        file_to_delete.touch()

        mock_controller.folder1_structure = [
            FileNode(file_to_delete)
        ]

        mock_results_tree = MagicMock()
        mock_update_status = MagicMock()

        mock_messagebox.askyesno.return_value = True

        delete_file(mock_controller, self.test_dir, "file1.txt", mock_results_tree, "iid1", mock_update_status)

        self.assertEqual(len(mock_controller.folder1_structure), 0)

    @patch('file_operations.messagebox')
    def test_delete_file_db(self, mock_messagebox):
        mock_controller = MagicMock()
        mock_controller.project_manager.current_project_path = self.db_path

        self.conn.execute("INSERT INTO files (path, name) VALUES (?, ?)", ("", "file1.txt"))
        self.conn.commit()

        file_to_delete = Path(self.test_dir) / "file1.txt"
        file_to_delete.touch()

        mock_results_tree = MagicMock()
        mock_update_status = MagicMock()

        mock_messagebox.askyesno.return_value = True

        delete_file(mock_controller, self.test_dir, "file1.txt", mock_results_tree, "iid1", mock_update_status)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files")
        self.assertEqual(len(cursor.fetchall()), 0)

    @patch('file_operations.messagebox')
    def test_move_file_json(self, mock_messagebox):
        mock_controller = MagicMock()
        mock_controller.project_manager.current_project_path = "test.cfp"
        mock_controller.folder1_path.get.return_value = self.test_dir
        mock_controller.folder2_path.get.return_value = ""

        file_to_move = Path(self.test_dir) / "file1.txt"
        file_to_move.touch()

        mock_controller.folder1_structure = [
            FileNode(file_to_move)
        ]

        mock_results_tree = MagicMock()
        mock_update_status = MagicMock()

        mock_messagebox.askyesno.return_value = True

        move_file(mock_controller, self.test_dir, "file1.txt", self.dest_dir, mock_results_tree, "iid1", mock_update_status)

        self.assertEqual(len(mock_controller.folder1_structure), 0)
        self.assertTrue((Path(self.dest_dir) / "file1.txt").exists())

    @patch('file_operations.messagebox')
    def test_move_file_db(self, mock_messagebox):
        mock_controller = MagicMock()
        mock_controller.project_manager.current_project_path = self.db_path

        self.conn.execute("INSERT INTO files (path, name) VALUES (?, ?)", ("", "file1.txt"))
        self.conn.commit()

        file_to_move = Path(self.test_dir) / "file1.txt"
        file_to_move.touch()

        mock_results_tree = MagicMock()
        mock_update_status = MagicMock()

        mock_messagebox.askyesno.return_value = True

        move_file(mock_controller, self.test_dir, "file1.txt", self.dest_dir, mock_results_tree, "iid1", mock_update_status)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files")
        self.assertEqual(len(cursor.fetchall()), 0)
        self.assertTrue((Path(self.dest_dir) / "file1.txt").exists())

if __name__ == '__main__':
    unittest.main()