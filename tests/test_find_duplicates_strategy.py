import unittest
from unittest.mock import MagicMock, patch
import sqlite3

from strategies import find_duplicates_strategy

class TestFindDuplicatesStrategy(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.create_test_tables()
        self.insert_test_data()

    def tearDown(self):
        self.conn.close()

    def create_test_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE files (
                    id INTEGER PRIMARY KEY,
                    folder_index INTEGER,
                    name TEXT,
                    path TEXT,
                    ext TEXT,
                    last_seen REAL
                )
            """)
            self.conn.execute("""
                CREATE TABLE file_metadata (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER,
                    size INTEGER,
                    modified_date REAL,
                    md5 TEXT,
                    histogram TEXT,
                    llm_embedding BLOB,
                    FOREIGN KEY (file_id) REFERENCES files(id)
                )
            """)

    def insert_test_data(self):
        files_data = [
            (1, 1, 'file1.txt', 'a', '.txt', 0),
            (2, 1, 'file2.txt', 'a', '.txt', 0),
            (3, 1, 'file3.txt', 'b', '.txt', 0),
            (4, 2, 'file1.txt', 'c', '.txt', 0),
            (5, 2, 'file4.txt', 'd', '.txt', 0),
        ]
        metadata_data = [
            (1, 1, 100, 12345.0, 'aaa', None, None),
            (2, 2, 200, 12345.0, 'bbb', None, None),
            (3, 3, 100, 54321.0, 'ccc', None, None),
            (4, 4, 100, 12345.0, 'aaa', None, None),
            (5, 5, 300, 67890.0, 'ddd', None, None),
        ]
        with self.conn:
            self.conn.executemany("INSERT INTO files VALUES (?,?,?,?,?,?)", files_data)
            self.conn.executemany("INSERT INTO file_metadata VALUES (?,?,?,?,?,?,?)", metadata_data)

    @patch('strategies.find_duplicates_strategy.get_strategy')
    def test_run(self, mock_get_strategy):
        # Mock the get_strategy function to return a mock strategy
        mock_strategy = MagicMock()
        mock_strategy.get_duplications_ids.return_value = [[1, 3, 4]]
        mock_get_strategy.return_value = mock_strategy

        opts = {'options': {'compare_size': True}}

        duplicates = find_duplicates_strategy.run(self.conn, opts)

        self.assertEqual(len(duplicates), 1)
        self.assertEqual(len(duplicates[0]), 3)

        # Check that the returned data is a list of dicts with the correct keys
        self.assertIsInstance(duplicates[0][0], dict)
        self.assertIn('id', duplicates[0][0])
        self.assertIn('name', duplicates[0][0])
        self.assertIn('size', duplicates[0][0])

        # Check that the correct file IDs are returned
        returned_ids = {d['id'] for d in duplicates[0]}
        self.assertEqual(returned_ids, {1, 3, 4})


if __name__ == '__main__':
    unittest.main()
