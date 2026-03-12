# Changelog

## Unreleased
### Added
- **Metric Caching Engine**: Implemented a 30-minute TTL SQLite-backed metric cache (`MetricCache`) in `src/services/cache_manager.py` to prevent redundant calculations across different comparison methods.
- **BaseCalculator Caching Layer**: Automated caching for all specific calculators (MD5, Histogram, Size, Date, Video Fast, Video Accurate) by refactoring `BaseCalculator` to implicitly fetch and store results inside the SQLite `metric_cache.db`.
- **Fuzzy Name Similarity**: Enhanced the `Name` comparison strategy to support configurable fuzzy filename matching. The threshold can be set from 0% to 100%; at 100% (default) it performs an exact case-insensitive stem match; below 100% it uses `difflib.SequenceMatcher` to compute a similarity ratio between the filename stems (without extension). This allows finding files with slightly different names (e.g. year variants, minor edits) without extra dependencies.

### Changed
- **Metric Cache TTL**: Increased the metric cache expiry from 30 minutes to **24 hours** (1440 minutes) in `src/services/cache_manager.py`. This retains expensive computed metrics (MD5, histograms, embeddings) across multiple sessions within the same day.

### Fixed
- **Source Folder Persistence Bug (improved)**: Strengthened the source folder save mechanism with two layers of protection: (1) `on_folders_changed` in `AppController` now normalizes paths via `Path.as_posix()` for consistent Windows path comparison, shows a user-visible status message on save, and displays an error dialog on failure instead of silently swallowing it. (2) `_save_project_db` in `ProjectManager` now also syncs the current source list from the UI listbox as a safety net — so File > Save always persists sources regardless of whether `on_folders_changed` triggered correctly.
- Fixed bug in unit tests (`test_find_duplicates_strategy.py`) where `file_metadata` schema changes caused sqlite `OperationalError` failures for missing video hash columns. Tests updated.
- Fixed a bug where similarity-only comparisons (like Video Accurate and Video Fast) caused file paths to be displayed incorrectly, preventing the UI Preview context menu action from working. Updated `utils.py` dictionary keys from `relative_path` to `path` to properly trace the file.
