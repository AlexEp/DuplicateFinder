# Changelog

## 2025-12-26
- **Refactor (Phase 1: Foundation & Abstractions)**: 
  - **Interfaces**: Introduced `IView`, `IFileRepository`, `IComparisonStrategy`, and `IMetadataCalculator` to enable Dependency Inversion.
  - **Domain Models**: Introduced `FileInfo` and `ComparisonOptions` immutable value objects for cleaner data handling.
  - **Repository Pattern**: Implemented `SQLiteRepository` to encapsulate database access.
  - **Decoupling**: Successfully broke the circular dependency between `ui.py` and `controller.py` by using the `IView` interface.
  - **Project Management**: Refactored `ProjectManager` and `AppController` to use the new domain-driven architecture.
  - **Maintenance**: Added `opencv-python` and confirmed requirement dependencies for testing.

## 2025-09-11
- **UX**: Comparison results for a pair of folders will no longer be shown if there are no matches between them.
- **Fix**: Corrected the comparison logic to ensure that when comparing folders, groups of all matching files from all involved folders are displayed, rather than just showing one side of the match.
- **UX**: The results view now displays the full path of each file instead of the relative path, providing clearer context for file locations.
- **Fix**: Corrected a bug that prevented the "Preview" feature from working. The full file path is now correctly passed to the UI, enabling the context menu option for supported file types.
- **Fix**: Refactored the duplicate finding strategy to unify the database and in-memory logic. This resolves a critical bug where duplicate finding in "Compare Mode" would fail due to a call to a removed function, ensuring that duplicate results are now accurate and consistently grouped in the UI.
- **Fix**: Fixed a bug where loading a project with an older database schema would cause a crash. The application now automatically creates missing tables when loading a project, ensuring backward compatibility.
- **Refactor**: Overhauled the comparison logic. The inefficient pairwise comparison in `logic.py` has been replaced with a high-performance hash-based algorithm. The redundant `get_duplications_ids` method has been removed from all comparison strategies, simplifying the design.
- **Fix**: Corrected a data flow issue where freshly calculated metadata (like MD5 hashes) was not used during the duplicate finding process. The controller now passes the in-memory metadata directly to the comparison strategy, ensuring accurate results.
- **Refactor**: Implemented multi-stage duplicate finding. The system now chains multiple comparison strategies (e.g., size, then MD5) to progressively refine results, providing much more accurate duplicate detection instead of relying on a single criterion.
- **Fix**: The "Find Duplicates by Size" query now ignores files with a size of 0, preventing large, irrelevant groups of empty files from cluttering the results.
- **Fix**: Optimized the database query for finding duplicates by size. The query now uses a single, more efficient `GROUP BY` and `GROUP_CONCAT` operation, preventing potential performance issues with large datasets and directly addressing the user's feedback.

## 2025-09-08
- **Refactor**: Normalized database schema by extracting `size`, `modified_date`, `md5`, `histogram`, and `llm_embedding` from the `files` table into a new `file_metadata` table.
  - `database.py`: Modified `create_tables` to define `file_metadata` and remove these columns from `files`. Updated `insert_file_node` to insert into both tables. Updated `get_all_files` to `JOIN` `files` and `file_metadata`.
  - `logic.py`: Modified `build_folder_structure_db` to perform individual UPSERT operations for `files` and `file_metadata`.
  - `strategies/utils.py`: Modified `calculate_metadata_db` to `JOIN` `files` and `file_metadata` for data retrieval and to update `file_metadata` directly.
  - `strategies/compare_by_date.py`: Corrected the key used for date comparison from `'date'` to `'modified_date'` to align with the database column name.
- **Fix**: Corrected a bug in `logic.py` where the database query to check for existing files was only checking the folder path and not the filename. This caused only one file per folder to be recorded. The query has been updated to include the filename, ensuring all files are correctly processed.

## 2025-09-07
- **Feature**: Modified database schema and logic to store only the directory path in `relative_path` column, improving data consistency. The UI now correctly reconstructs and displays the full relative path.
- **Fix**: Resolved `sqlite3.IntegrityError: UNIQUE constraint failed: sources.path` when creating a new project with an existing file name by clearing existing sources before adding new ones.
- **UX**: Removed the 'Add/Remove Folder' buttons from the main window to simplify the UI.
- **Fix**: The "X" button on the 'New Project' window now correctly closes the window.
- **UX**: Increased the default size of the 'New Project' window for better usability.

## 2025-09-05
- **Fix**: Fixed the "Compare by Name" functionality in the "Compare Folders" mode. A dedicated comparison strategy for names was created and registered, ensuring that the feature works as intended.
- **Fix**: Corrected the file type filtering logic. The application now correctly filters files based on the selected file type (Image, Video, Document, All) in both JSON and SQLite-based projects.

## 2025-09-04
- **Fix**: Corrected a bug preventing comparisons from running on projects using the older `.cfp` (JSON) format. The data structure returned after metadata calculation for JSON projects now correctly matches the format expected by the comparison strategies.

## 2025-09-03
- **Refactor**: Migrated project data storage from JSON to SQLite for improved performance, scalability, and data integrity.
  - Introduced a new `.cfp-db` project format based on SQLite.
  - Created a `database.py` module to handle all database operations.
  - Refactored `project_manager.py`, `logic.py`, and `controller.py` to support both JSON and SQLite project formats.
  - Updated comparison strategies to work with data from the SQLite database.

## 2025-09-03
- **Responsiveness**: Refactored long-running operations to execute in background threads, preventing the UI from freezing.
  - Implemented a `TaskRunner` utility to manage background tasks and communicate with the main UI thread safely.
  - The initial metadata build (`build_folder_structure`) now runs in the background.
  - The main "Compare" and "Find Duplicates" action, including metadata calculation (`flatten_structure`) and strategy execution, now runs in the background.
  - UI components (buttons, status bar) are disabled and updated appropriately during background processing.

## 2025-09-03
- **UX/Readability**: Implemented several UI/UX and code readability improvements.
  - Added tooltips to all major buttons and options to clarify their function.
  - Implemented keyboard shortcuts for common actions: `Ctrl+B` to build metadata and `Ctrl+R` to run the main action.
  - Refactored UI code in `ui.py` to reduce duplication, particularly in file operation and context menu logic.
  - Enhanced error feedback by collecting and displaying a list of inaccessible files/folders to the user after the build process.

## 2025-09-02
- **Feature**: Decoupled LLM similarity threshold from the histogram threshold, adding a dedicated input field in the UI.
- **Refactor**: Removed the non-functional "Search" mode to simplify the user interface.
- **UX**: Added a performance warning when running a "Find Duplicates" action using only the "Histogram" comparison, which can be very slow.

## 2025-09-02

-   **Improved LLM Testing Strategy**:
    -   Refactored `tests/test_llm_similarity.py` to remove dependency on the external `instraction.txt` file, making tests self-contained and more robust.
    -   Strengthened assertions to check for similarity scores within a specific range for "similar but not the same" cases.
    -   Mocked the `LlavaEmbeddingEngine` during tests to significantly improve test execution speed and remove the need for actual model files during the test run.

## 2025-09-02

- **Perf**: Implemented performance optimizations.
  - The application now avoids recalculating existing metadata (MD5, Histogram, LLM embeddings) by caching these values in the project file.
  - The LLM engine is now lazy-loaded in a background thread upon first use, significantly improving application startup time.
- **Fix**: Corrected a latent bug in how metadata was stored, ensuring all metadata is consistently saved in the `metadata` dictionary within the project file.

## 2025-09-02

- **Refactor**: Improved code organization and removed duplication.
  - Removed duplicate method definitions for `_preview_file` and `_get_relative_path_from_selection` in `ui.py`.
  - Consolidated UI creation logic in `ui.py` by creating a factory method (`_create_folder_selection_frame`) for the folder selection frames, reducing repeated code.
  - Moved the generic `_find_connected_components` graph algorithm from `strategies/find_duplicates_strategy.py` to a new, more appropriate `utils/graph_utils.py` module.

## 2025-09-01

- **Refactor**: Centralized configuration management.
  - Introduced a singleton `Config` class in `config.py` to manage all application settings.
  - Consolidated settings from `settings.json` and `llm_settings.json` into the `Config` object.
  - Moved hardcoded model paths from `ai_engine/engine.py` to `settings.json`.
  - Moved hardcoded file extension lists from `strategies/utils.py` to `settings.json`.
  - Refactored all modules (`ui.py`, `logger_config.py`, etc.) to source configuration from the new `Config` class, removing direct file reads.
- **Fix**: Made LLM-related tests skippable based on configuration.
  - The `test_llm_similarity` test suite will now be skipped if `use_llm` is `false` in the application settings, preventing test failures in environments without the LLM components.

## 2025-08-31

- **Feature**: Added application-wide logging.
  - Logs are configured in a new `logger_config.py` module.
  - Log level is determined by the `log_level` setting in `settings.json`.
  - Log files are created daily in the `logs/` directory with the format `YYYYMMDD.log`.
  - Key application events, errors, and user actions are now logged.

## 2025-08-31

- **Feature**: Add LLM-powered image similarity engine.
  - Integrates a LLaVA model to perform semantic comparison of images.
  - Adds a new "LLM Content" comparison option.
  - The engine runs locally and requires users to download model files (see `models/README.md`).
  - This is a resource-intensive feature and works best with GPU acceleration.


## 2025-08-30

- **Feat**: Add preview functionality to context menu.
- **Fix**: Fix context menu functionality.
- **Fix**: Corrected the logic for displaying preview options in the context menu.
- **Feat**: Added support for .flv and .wmv video file previews.

## 2024-07-15
- **Feature**: Add preview for media files.
  - Adds a "Preview" option to the right-click context menu for image, video, and audio files.
  - Images are displayed in a new window.
  - Audio/video files are opened with the default system player.
- **Feature**: Display comparison results in a grid.
  - The results view now shows file name, size, and relative path in a grid format.
  - This provides more information at a glance and is easier to read.
- Initial creation of the changelog.