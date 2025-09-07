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

    def tearDown(self):
        shutil.rmtree(self.test_dir)

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

        conn = sqlite3.connect(self.db_path)
        from database import create_tables, delete_file_by_path
        create_tables(conn)
        conn.execute("INSERT INTO files (relative_path) VALUES (?)", ("file1.txt",))
        conn.commit()

        file_to_delete = Path(self.test_dir) / "file1.txt"
        file_to_delete.touch()

        mock_results_tree = MagicMock()
        mock_update_status = MagicMock()

        mock_messagebox.askyesno.return_value = True

        delete_file(mock_controller, self.test_dir, "file1.txt", mock_results_tree, "iid1", mock_update_status)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files")
        self.assertEqual(len(cursor.fetchall()), 0)
        conn.close()

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

        conn = sqlite3.connect(self.db_path)
        from database import create_tables, delete_file_by_path
        create_tables(conn)
        conn.execute("INSERT INTO files (relative_path) VALUES (?)", ("file1.txt",))
        conn.commit()

        file_to_move = Path(self.test_dir) / "file1.txt"
        file_to_move.touch()

        mock_results_tree = MagicMock()
        mock_update_status = MagicMock()

        mock_messagebox.askyesno.return_value = True

        move_file(mock_controller, self.test_dir, "file1.txt", self.dest_dir, mock_results_tree, "iid1", mock_update_status)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files")
        self.assertEqual(len(cursor.fetchall()), 0)
        conn.close()
        self.assertTrue((Path(self.dest_dir) / "file1.txt").exists())

if __name__ == '__main__':
    unittest.main()