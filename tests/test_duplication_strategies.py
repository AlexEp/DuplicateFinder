import unittest
from unittest.mock import MagicMock, patch
import sqlite3

from strategies.size.comparator import CompareBySize
from strategies.date.comparator import CompareByDate
from strategies.md5.comparator import CompareByContentMD5
from strategies.name.comparator import CompareByNameStrategy

class TestDuplicationStrategies(unittest.TestCase):

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
            (1, 1, 100, 12345.0, 'aaa'),
            (2, 2, 200, 12345.0, 'bbb'),
            (3, 3, 100, 54321.0, 'ccc'),
            (4, 4, 100, 12345.0, 'aaa'),
            (5, 5, 300, 67890.0, 'ddd'),
        ]
        with self.conn:
            self.conn.executemany("INSERT INTO files VALUES (?,?,?,?,?,?)", files_data)
            self.conn.executemany("INSERT INTO file_metadata VALUES (?,?,?,?,?)", metadata_data)

    def test_get_duplications_by_size(self):
        strategy = CompareBySize()
        duplicates = strategy.get_duplications_ids(self.conn)
        self.assertEqual(len(duplicates), 1)
        self.assertCountEqual(duplicates[0], [1, 3, 4])

    def test_get_duplications_by_date(self):
        strategy = CompareByDate()
        duplicates = strategy.get_duplications_ids(self.conn)
        self.assertEqual(len(duplicates), 1)
        self.assertCountEqual(duplicates[0], [1, 2, 4])

    def test_get_duplications_by_md5(self):
        strategy = CompareByContentMD5()
        duplicates = strategy.get_duplications_ids(self.conn)
        self.assertEqual(len(duplicates), 1)
        self.assertCountEqual(duplicates[0], [1, 4])

    def test_get_duplications_by_name(self):
        strategy = CompareByNameStrategy()
        duplicates = strategy.get_duplications_ids(self.conn)
        self.assertEqual(len(duplicates), 1)
        self.assertCountEqual(duplicates[0], [1, 4])

if __name__ == '__main__':
    unittest.main()
