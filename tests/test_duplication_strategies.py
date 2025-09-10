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

    def test_get_duplications_with_nulls(self):
        # Insert some data with NULLs
        with self.conn:
            self.conn.execute("INSERT INTO files VALUES (?,?,?,?,?,?)", (6, 1, 'null_size.txt', 'e', '.txt', 0))
            self.conn.execute("INSERT INTO file_metadata VALUES (?,?,?,?,?,?,?)", (6, 6, None, 666, 'eee', None, None))
            self.conn.execute("INSERT INTO files VALUES (?,?,?,?,?,?)", (7, 1, 'null_date.txt', 'f', '.txt', 0))
            self.conn.execute("INSERT INTO file_metadata VALUES (?,?,?,?,?,?,?)", (7, 7, 700, None, 'fff', None, None))
            self.conn.execute("INSERT INTO files VALUES (?,?,?,?,?,?)", (8, 1, 'null_md5.txt', 'g', '.txt', 0))
            self.conn.execute("INSERT INTO file_metadata VALUES (?,?,?,?,?,?,?)", (8, 8, 800, 888, None, None, None))
            self.conn.execute("INSERT INTO files VALUES (?,?,?,?,?,?)", (9, 1, None, 'h', '.txt', 0))
            self.conn.execute("INSERT INTO file_metadata VALUES (?,?,?,?,?,?,?)", (9, 9, 900, 999, 'ggg', None, None))
            # Add another NULL size to make a potential duplicate group
            self.conn.execute("INSERT INTO files VALUES (?,?,?,?,?,?)", (10, 1, 'null_size_2.txt', 'i', '.txt', 0))
            self.conn.execute("INSERT INTO file_metadata VALUES (?,?,?,?,?,?,?)", (10, 10, None, 666, 'eee', None, None))

        # Test that NULLs are not considered duplicates
        size_strategy = CompareBySize()
        size_duplicates = size_strategy.get_duplications_ids(self.conn)
        self.assertNotIn([6, 10], size_duplicates)

        date_strategy = CompareByDate()
        date_duplicates = date_strategy.get_duplications_ids(self.conn)
        # Check that file 7 is not in any group
        self.assertFalse(any(7 in group for group in date_duplicates))

        md5_strategy = CompareByContentMD5()
        md5_duplicates = md5_strategy.get_duplications_ids(self.conn)
        self.assertFalse(any(8 in group for group in md5_duplicates))

        name_strategy = CompareByNameStrategy()
        name_duplicates = name_strategy.get_duplications_ids(self.conn)
        self.assertFalse(any(9 in group for group in name_duplicates))

if __name__ == '__main__':
    unittest.main()
