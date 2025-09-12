import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import unittest
from strategies.size.comparator import CompareBySize
from strategies.date.comparator import CompareByDate
from strategies.md5.comparator import CompareByContentMD5
from strategies.name.comparator import CompareByNameStrategy

class TestComparisonStrategies(unittest.TestCase):

    def test_compare_by_size(self):
        strategy = CompareBySize()
        # Test case: Sizes are equal
        self.assertTrue(strategy.compare({'size': 100}, {'size': 100}))

        # Test case: Sizes are not equal
        self.assertFalse(strategy.compare({'size': 100}, {'size': 200}))

        # Test case: Key missing in one dictionary
        self.assertFalse(strategy.compare({'size': 100}, {}))

        # Test case: Key missing in both dictionaries
        self.assertFalse(strategy.compare({}, {}))

    def test_compare_by_date(self):
        strategy = CompareByDate()
        # Test case: Dates are equal
        self.assertTrue(strategy.compare({'modified_date': 12345.67}, {'modified_date': 12345.67}))

        # Test case: Dates are not equal
        self.assertFalse(strategy.compare({'modified_date': 12345.67}, {'modified_date': 76543.21}))

        # Test case: Key missing in one dictionary
        self.assertFalse(strategy.compare({'modified_date': 12345.67}, {}))

        # Test case: Key missing in both dictionaries
        self.assertFalse(strategy.compare({}, {}))

    def test_compare_by_content_md5(self):
        strategy = CompareByContentMD5()
        hash1 = "a" * 32
        hash2 = "b" * 32
        key = 'md5'

        # Test case: Hashes are equal
        self.assertTrue(strategy.compare({key: hash1}, {key: hash1}))

        # Test case: Hashes are not equal
        self.assertFalse(strategy.compare({key: hash1}, {key: hash2}))

        # Test case: Key missing in one dictionary
        self.assertFalse(strategy.compare({key: hash1}, {}))

        # Test case: Key missing in both dictionaries
        self.assertFalse(strategy.compare({}, {}))

        # Test case: One hash is None (e.g., failed to calculate)
        self.assertFalse(strategy.compare({key: hash1}, {key: None}))
        self.assertFalse(strategy.compare({key: None}, {key: hash1}))
        self.assertFalse(strategy.compare({key: None}, {key: None}))

    def test_compare_by_name(self):
        strategy = CompareByNameStrategy()
        # Test case: Names are equal
        self.assertTrue(strategy.compare({'relative_path': 'file1.txt'}, {'relative_path': 'file1.txt'}))

        # Test case: Names are not equal
        self.assertFalse(strategy.compare({'relative_path': 'file1.txt'}, {'relative_path': 'file2.txt'}))

        # Test case: Key missing in one dictionary
        self.assertFalse(strategy.compare({'relative_path': 'file1.txt'}, {}))

        # Test case: Key missing in both dictionaries
        self.assertFalse(strategy.compare({}, {}))

if __name__ == '__main__':
    unittest.main()
