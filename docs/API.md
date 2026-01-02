# DuplicateFinder API Documentation

This document outlines the public interfaces and services available in the DuplicateFinder application.

## Core Interfaces

### `IView`
Located in `src/interfaces/view_interface.py`.
- `update_status(message, progress_value=None)`: Update the UI status bar and optional progress bar.
- `show_error(title, message)`: Display an error dialog.
- `show_info(title, message)`: Display an informational dialog.
- `display_results(results)`: Show comparison or duplicate results.
- `remove_result_item(item_id)`: Remove a specific row from the results view.

### `IFileRepository`
Located in `src/interfaces/repository_interface.py`.
- `get_all_files(folder_index, file_type_filter="all")`: Retrieve all files for a given folder source.
- `get_files_by_ids(ids)`: Retrieve specific files by their database IDs.
- `save_file_metadata_batch(metadata_list)`: Perform an efficient batch update of file metadata.

## Services

### `ProjectService`
Located in `src/services/project_service.py`.
- `save_settings(options)`: Persist current comparison options.
- `load_settings()`: Retrieve persisted options.
- `sync_folders(folder_indices, include_subfolders=True)`: Synchronize the local filesystem with the database.

### `ComparisonService`
Located in `src/services/comparison_service.py`.
- `compare_folders(folder_indices, options)`: Find common files across multiple folders.
- `find_duplicates(folder_indices, options, file_infos=None)`: Find duplicate files within the specified folders.

### `FileService`
Located in `src/services/file_service.py`.
- `scan_folder(path, include_subfolders=True)`: Return a list of files from the disk.
- `delete_file(path)`: Permanently delete a file from the disk.
- `move_file(source, destination)`: Move a file to a new location.
- `open_folder(path)`: Open the system file explorer at the given path.
