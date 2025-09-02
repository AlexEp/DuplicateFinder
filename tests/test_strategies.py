import unittest
from strategies import compare_by_size, compare_by_date, compare_by_content_md5

class TestComparisonStrategies(unittest.TestCase):

    def test_compare_by_size(self):
        # Test case: Sizes are equal
        self.assertTrue(compare_by_size.compare({'compare_size': 100}, {'compare_size': 100}))

        # Test case: Sizes are not equal
        self.assertFalse(compare_by_size.compare({'compare_size': 100}, {'compare_size': 200}))

        # Test case: Key missing in one dictionary
        self.assertFalse(compare_by_size.compare({'compare_size': 100}, {}))

        # Test case: Key missing in both dictionaries
        self.assertFalse(compare_by_size.compare({}, {}))

    def test_compare_by_date(self):
        # Test case: Dates are equal
        self.assertTrue(compare_by_date.compare({'compare_date': 12345.67}, {'compare_date': 12345.67}))

        # Test case: Dates are not equal
        self.assertFalse(compare_by_date.compare({'compare_date': 12345.67}, {'compare_date': 76543.21}))

        # Test case: Key missing in one dictionary
        self.assertFalse(compare_by_date.compare({'compare_date': 12345.67}, {}))

        # Test case: Key missing in both dictionaries
        self.assertFalse(compare_by_date.compare({}, {}))

    def test_compare_by_content_md5(self):
        hash1 = "a" * 32
        hash2 = "b" * 32
        key = 'compare_content_md5'

        # Test case: Hashes are equal
        self.assertTrue(compare_by_content_md5.compare({'metadata': {key: hash1}}, {'metadata': {key: hash1}}))

        # Test case: Hashes are not equal
        self.assertFalse(compare_by_content_md5.compare({'metadata': {key: hash1}}, {'metadata': {key: hash2}}))

        # Test case: Key missing in one dictionary
        self.assertFalse(compare_by_content_md5.compare({'metadata': {key: hash1}}, {}))
        self.assertFalse(compare_by_content_md5.compare({'metadata': {key: hash1}}, {'metadata': {}}))


        # Test case: Key missing in both dictionaries
        self.assertFalse(compare_by_content_md5.compare({}, {}))

        # Test case: One hash is None (e.g., failed to calculate)
        self.assertFalse(compare_by_content_md5.compare({'metadata': {key: hash1}}, {'metadata': {key: None}}))
        self.assertFalse(compare_by_content_md5.compare({'metadata': {key: None}}, {'metadata': {key: hash1}}))
        self.assertFalse(compare_by_content_md5.compare({'metadata': {key: None}}, {'metadata': {key: None}}))

if __name__ == '__main__':
    unittest.main()
