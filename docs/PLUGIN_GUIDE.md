# DuplicateFinder Plugin Guide

DuplicateFinder is designed for extensibility. You can add new file comparison methods by implementing the strategy interfaces.

## How to Add a New Comparison Option

Adding a new comparison option requires three steps:

### 1. Create the Strategy Files
Create a new directory in `src/strategies/` for your strategy (e.g., `exif`):
- `src/strategies/exif/calculator.py`: Handles metadata calculation (e.g., extracting EXIF data).
- `src/strategies/exif/comparator.py`: Handles the actual comparison between two files' EXIF data.

### 2. Implement the Metadata and Comparison
Your comparator class must inherit from `BaseComparisonStrategy` and provide `StrategyMetadata`:

```python
from strategies.base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata

class ExifComparator(BaseComparisonStrategy):
    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_exif',
            display_name='EXIF Data',
            description='Compare camera metadata',
            tooltip='Compares EXIF data like camera model and date taken.',
            requires_calculation=True,
            has_threshold=False
        )
    
    @property
    def db_key(self) -> str:
        return 'exif_data' # Column in your specialized table

    def compare(self, file1_info, file2_info, opts=None) -> bool:
        # Implementation logic here
        pass
```

### 3. Register the Strategy
Register your new strategy in `src/strategies/strategy_registry.py`. Once registered, the UI will **automatically** generate a checkbox for it in the Settings Panel.

## Dynamic UI Generation
The `SettingsPanel` uses the `StrategyMetadata` to create:
- **Checkboxes**: Automatically added based on `option_key` and `display_name`.
- **Tooltips**: Added from the `tooltip` field.
- **Threshold Inputs**: If `has_threshold` is True, a numeric input will be added.

## Metadata Caching
If your strategy requires expensive calculation (like hashing or AI embeddings), implement an `IMetadataCalculator` and integrate it with `utils.calculate_metadata_db`. The system will automatically cache these values and only recalculate them if the file size or modification date changes.
