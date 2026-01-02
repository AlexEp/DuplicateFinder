# Changelog

## [2.1.0] - 2026-01-01

### Added
- Service Layer architecture (`FileService`, `ComparisonService`, `ProjectService`).
- Standardized Error Handling system with custom exceptions.
- Input validation module (`PathValidator`, `ComparisonValidator`).
- Comprehensive documentation in `docs/` (Architecture, API, Plugin Guide).
- Batch database operation support for metadata persistence.

### Changed
- Refactored `AppController` to use DI and services.
- Refactored `FolderComparisonApp` to use standardized UI state management.
- Moved file operations (move, delete, open folder) from utility functions to `FileService`.
- Updated test suite to work with the new service-based architecture.

### Removed
- `src/file_operations.py` (replaced by `FileService` and `AppController` methods).
- `tests/test_file_operations.py` (obsolete).

## [2.0.0] - Previous Refactorings
- Phase 1-3 improvements (refer to earlier logs/documentation).
