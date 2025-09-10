import unittest
import sqlite3

from strategies import find_duplicates_strategy
from strategies.strategy_registry import discover_strategies, clear_strategies

class TestFindDuplicatesStrategy(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.create_test_tables()
        self.insert_test_data()
        # Ensure strategies are discovered for the test
        clear_strategies()
        discover_strategies()

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
            (1, 1, 'file1.txt', 'a', '.txt', 0), # Dup size, date, md5, name with 4
            (2, 1, 'file2.txt', 'a', '.txt', 0), # Dup date with 1, 4
            (3, 1, 'file3.txt', 'b', '.txt', 0), # Dup size with 1, 4
            (4, 2, 'file1.txt', 'c', '.txt', 0), # Dup size, date, md5, name with 1
            (5, 2, 'file4.txt', 'd', '.txt', 0),
            (6, 1, 'file5.txt', 'e', '.txt', 0), # Dup size and date with 7
            (7, 2, 'file6.txt', 'f', '.txt', 0), # Dup size and date with 6
        ]
        metadata_data = [
            (1, 1, 100, 12345.0, 'aaa', None, None),
            (2, 2, 200, 12345.0, 'bbb', None, None),
            (3, 3, 100, 54321.0, 'ccc', None, None),
            (4, 4, 100, 12345.0, 'aaa', None, None),
            (5, 5, 300, 67890.0, 'ddd', None, None),
            (6, 6, 500, 77777.0, 'eee', None, None),
            (7, 7, 500, 77777.0, 'fff', None, None),
        ]
        with self.conn:
            self.conn.executemany("INSERT INTO files VALUES (?,?,?,?,?,?)", files_data)
            self.conn.executemany("INSERT INTO file_metadata VALUES (?,?,?,?,?,?,?)", metadata_data)

    def test_run_with_single_criterion_size(self):
        opts = {'compare_size': True}
        duplicates = find_duplicates_strategy.run(self.conn, opts)

        self.assertEqual(len(duplicates), 2)
        # Find the group with [1, 3, 4]
        group1 = next((g for g in duplicates if {d['id'] for d in g} == {1, 3, 4}), None)
        self.assertIsNotNone(group1)
        # Find the group with [6, 7]
        group2 = next((g for g in duplicates if {d['id'] for d in g} == {6, 7}), None)
        self.assertIsNotNone(group2)

    def test_run_with_single_criterion_date(self):
        opts = {'compare_date': True}
        duplicates = find_duplicates_strategy.run(self.conn, opts)

        self.assertEqual(len(duplicates), 2)
        # Find the group with [1, 2, 4]
        group1 = next((g for g in duplicates if {d['id'] for d in g} == {1, 2, 4}), None)
        self.assertIsNotNone(group1)
        # Find the group with [6, 7]
        group2 = next((g for g in duplicates if {d['id'] for d in g} == {6, 7}), None)
        self.assertIsNotNone(group2)


if __name__ == '__main__':
    unittest.main()
