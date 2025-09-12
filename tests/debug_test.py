import unittest
import sqlite3
from strategies.size.comparator import CompareBySize

class DebugTest(unittest.TestCase):
    def test_debug_get_duplications_by_size(self):
        conn = sqlite3.connect(":memory:")
        with conn:
            conn.execute("""
                CREATE TABLE files (id INTEGER PRIMARY KEY, name TEXT)
            """)
            conn.execute("""
                CREATE TABLE file_metadata (id INTEGER PRIMARY KEY, file_id INTEGER, size INTEGER)
            """)
            conn.executemany("INSERT INTO files (id, name) VALUES (?,?)", [(1, 'a'), (2, 'b'), (3, 'c')])
            conn.executemany("INSERT INTO file_metadata (file_id, size) VALUES (?,?)", [(1, 100), (2, 200), (3, 100)])

        strategy = CompareBySize()
        duplicates = strategy.get_duplications_ids(conn)

        self.assertEqual(len(duplicates), 1)
        self.assertCountEqual(duplicates[0], [1, 3])

        conn.close()

if __name__ == '__main__':
    unittest.main()
