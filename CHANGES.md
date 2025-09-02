# Changelog

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