# Changelog

## Unreleased
### Added
- **Metric Caching Engine**: Implemented a 30-minute TTL SQLite-backed metric cache (`MetricCache`) in `src/services/cache_manager.py` to prevent redundant calculations across different comparison methods.
- **BaseCalculator Caching Layer**: Automated caching for all specific calculators (MD5, Histogram, Size, Date, Video Fast, Video Accurate) by refactoring `BaseCalculator` to implicitly fetch and store results inside the SQLite `metric_cache.db`.

### Fixed
- Fixed bug in unit tests (`test_find_duplicates_strategy.py`) where `file_metadata` schema changes caused sqlite `OperationalError` failures for missing video hash columns. Tests updated.
- Fixed a bug where similarity-only comparisons (like Video Accurate and Video Fast) caused file paths to be displayed incorrectly, preventing the UI Preview context menu action from working. Updated `utils.py` dictionary keys from `relative_path` to `path` to properly trace the file.
