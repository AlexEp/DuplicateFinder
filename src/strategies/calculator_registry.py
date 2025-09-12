import importlib
import pkgutil
from .base_calculator import BaseCalculator

_CALCULATORS = {}

def register_calculator(calculator_class):
    """
    Registers a new calculator.
    """
    if not issubclass(calculator_class, BaseCalculator):
        raise ValueError("Calculator must be a subclass of BaseCalculator")

    instance = calculator_class()
    # We don't have an option_key for calculators, so we'll just store the instance.
    # We can use the class name as the key if we need to look them up.
    _CALCULATORS[calculator_class.__name__] = instance

def get_calculators():
    """
    Returns a list of all registered calculator instances.
    """
    return list(_CALCULATORS.values())

def discover_calculators():
    """
    Discovers and registers all calculators in the 'strategies' directory.
    """
    import strategies

    for _, name, _ in pkgutil.walk_packages(strategies.__path__, strategies.__name__ + '.'):
        if 'calculator' in name and 'base' not in name and 'registry' not in name:
            module = importlib.import_module(name)
            for item in dir(module):
                obj = getattr(module, item)
                if isinstance(obj, type) and issubclass(obj, BaseCalculator) and obj is not BaseCalculator:
                    register_calculator(obj)

# Discover calculators on import
discover_calculators()
