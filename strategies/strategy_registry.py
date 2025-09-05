import inspect
import pkgutil
from .base_comparison_strategy import BaseComparisonStrategy

class StrategyRegistry:
    def __init__(self):
        self.strategies = {}
        self._discover_strategies()

    def _discover_strategies(self):
        """Automatically discovers and registers all comparison strategies."""
        import strategies.compare_by_size
        import strategies.compare_by_date
        import strategies.compare_by_content_md5
        import strategies.compare_by_llm

        for importer, modname, ispkg in pkgutil.iter_modules(strategies.__path__):
            if modname.startswith('compare_by_'):
                module = __import__(f"strategies.{modname}", fromlist=["*"])
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseComparisonStrategy) and obj is not BaseComparisonStrategy:
                        instance = obj()
                        self.strategies[instance.option_key] = instance

    def get_active_strategies(self, opts):
        """Returns a list of active strategies based on the options."""
        active_strategies = []
        for key, strategy in self.strategies.items():
            if opts.get(key):
                active_strategies.append(strategy)
        return active_strategies

# Create a single instance of the registry to be used by the application
strategy_registry = StrategyRegistry()
