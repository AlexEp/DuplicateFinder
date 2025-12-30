import os
import sys
import unittest
import tkinter as tk
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from strategies.strategy_registry import get_all_strategies, get_strategy
from domain.comparison_options import ComparisonOptions
from strategies.base_comparison_strategy import StrategyMetadata

class TestPhase3Extensibility(unittest.TestCase):

    def test_strategy_metadata(self):
        """Test that all strategies have valid metadata."""
        strategies = get_all_strategies()
        self.assertGreater(len(strategies), 0)
        
        for strategy in strategies:
            meta = strategy.metadata
            self.assertIsInstance(meta, StrategyMetadata)
            self.assertIsNotNone(meta.option_key)
            self.assertIsNotNone(meta.display_name)
            self.assertIsNotNone(meta.tooltip)

    def test_dynamic_discovery(self):
        """Test that dummy strategy is discovered."""
        strategy = get_strategy('compare_dummy')
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.__class__.__name__, 'DummyStrategy')
        self.assertEqual(strategy.metadata.display_name, 'Dummy Strategy')

    def test_dynamic_options(self):
        """Test ComparisonOptions fallback and set/get."""
        opts = ComparisonOptions()
        
        # Test backward compatibility via __getattr__
        self.assertEqual(opts.compare_size, True)
        self.assertEqual(opts.compare_name, False)
        
        # Test setting new option
        opts.options['compare_foo'] = True
        self.assertEqual(opts.compare_foo, True)
        
        # Test from_dict
        data = {
            'file_type_filter': 'image',
            'options': {
                'include_subfolders': False,
                'compare_new': True,
                'new_threshold': 0.5
            }
        }
        opts2 = ComparisonOptions.from_dict(data)
        self.assertEqual(opts2.file_type_filter, 'image')
        self.assertEqual(opts2.include_subfolders, False)
        self.assertEqual(opts2.options['compare_new'], True)
        self.assertEqual(opts2.compare_new, True)
        self.assertEqual(opts2.new_threshold, 0.5)

if __name__ == '__main__':
    unittest.main()
