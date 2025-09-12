import importlib
import pkgutil
from .base_comparison_strategy import BaseComparisonStrategy

_STRATEGIES = {}

def clear_strategies():
    """
    Clears the strategy registry.
    """
    _STRATEGIES.clear()

def register_strategy(strategy_class):
    """
    Registers a new comparison strategy.
    """
    if not issubclass(strategy_class, BaseComparisonStrategy):
        raise ValueError("Strategy must be a subclass of BaseComparisonStrategy")

    instance = strategy_class()
    _STRATEGIES[instance.option_key] = instance

def get_strategy(option_key):
    """
    Returns a strategy instance for the given option key.
    """
    return _STRATEGIES.get(option_key)

def discover_strategies():
    """
    Discovers and registers all strategies in the 'strategies' directory.
    """
    import strategies

    for _, name, _ in pkgutil.walk_packages(strategies.__path__, strategies.__name__ + '.'):
        if 'comparator' in name:
            module = importlib.import_module(name)
            for item in dir(module):
                obj = getattr(module, item)
                if isinstance(obj, type) and issubclass(obj, BaseComparisonStrategy) and obj is not BaseComparisonStrategy:
                    register_strategy(obj)

# Discover strategies on import
discover_strategies()
