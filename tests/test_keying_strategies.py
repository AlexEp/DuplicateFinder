import unittest
from pathlib import Path
from strategies import key_by_size, key_by_date, key_by_content_md5

class TestKeyingStrategies(unittest.TestCase):

    def test_key_by_size(self):
        # Test case: Key exists
        self.assertEqual(key_by_size.get_key(None, {'size': 12345}), 12345)

        # Test case: Key is missing
        self.assertIsNone(key_by_size.get_key(None, {}))

    def test_key_by_date(self):
        # Test case: Key exists
        self.assertEqual(key_by_date.get_key(None, {'modified_date': 54321.0}), 54321.0)

        # Test case: Key is missing
        self.assertIsNone(key_by_date.get_key(None, {}))

    def test_key_by_content_md5(self):
        hash_val = "c" * 32
        # Test case: Key exists
        self.assertEqual(key_by_content_md5.get_key(None, {'md5': hash_val}), hash_val)

        # Test case: Key is missing
        self.assertIsNone(key_by_content_md5.get_key(None, {}))

        # Test case: Value is None
        self.assertIsNone(key_by_content_md5.get_key(None, {'md5': None}))

if __name__ == '__main__':
    unittest.main()
