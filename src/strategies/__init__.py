from . import calculator_registry
from . import strategy_registry

calculator_registry.discover_calculators()
strategy_registry.discover_strategies()
