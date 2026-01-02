# Agent Documentation

## Major Changes (Phase 4)

- **Service Layer**: Introduced `FileService`, `ComparisonService`, and `ProjectService` to encapsulate domain logic.
- **Dependency Injection**: Refactored `AppController` to accept services as dependencies, improving testability.
- **Error Handling**: Standardized error management with custom exceptions and validation.
- **Database Optimization**: Implemented `save_file_metadata_batch` for efficient updates.
- **Documentation**: Created `docs/` directory with detailed architectural and technical guides.

## Guidelines for Future Agents

- **Services**: Always move filesystem or heavy business logic to the appropriate Service class.
- **Interfaces**: Ensure any new major component implements an interface in `src/interfaces/`.
- **Testing**: Run `python -m unittest discover tests` after any architectural changes. Use `HeadlessAppController` for testing logic without a GUI.
- **Plugins**: To add new comparison methods, see `docs/PLUGIN_GUIDE.md`.
