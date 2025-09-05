import unittest
import sqlite3
from pathlib import Path
import os
from unittest.mock import MagicMock

from database import create_tables, save_setting, load_setting, clear_folder_data, insert_file_node, get_all_files
from models import FileNode

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db_path = "test.db"
        # Create a temporary file to be used by the tests
        self.temp_file_path = Path("/tmp/test_db_file.txt")
        self.temp_file_path.parent.mkdir(exist_ok=True)
        self.temp_file_path.touch()
        self.conn = sqlite3.connect(self.db_path)
        create_tables(self.conn)

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)
        os.remove(self.temp_file_path)

    def test_create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_settings'")
        self.assertIsNotNone(cursor.fetchone())
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
        self.assertIsNotNone(cursor.fetchone())

    def test_settings(self):
        save_setting(self.conn, "test_key", {"foo": "bar"})
        setting = load_setting(self.conn, "test_key")
        self.assertEqual(setting, {"foo": "bar"})

    def test_clear_folder_data(self):
        file_node = FileNode(self.temp_file_path, root_path=self.temp_file_path.parent)
        insert_file_node(self.conn, file_node, 1)
        clear_folder_data(self.conn, 1)
        files = get_all_files(self.conn, 1)
        self.assertEqual(len(files), 0)

    def test_insert_and_get_files(self):
        file_node = FileNode(self.temp_file_path, root_path=self.temp_file_path.parent)
        insert_file_node(self.conn, file_node, 1)
        files = get_all_files(self.conn, 1)
        self.assertEqual(len(files), 1)
        # The result from DB is a tuple, not a dict
        self.assertIn('test_db_file.txt', files[0])


if __name__ == '__main__':
    unittest.main()
