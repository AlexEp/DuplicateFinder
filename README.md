# Folder Comparison and Duplicate Finder Tool

This tool provides a graphical user interface (GUI) to compare two folders or find duplicate files within a single folder. It is built using Python's Tkinter library.

The application supports various comparison strategies and can be extended with new ones. It uses a project-based approach, allowing users to save their settings and folder metadata for later use.

## Features

- **Compare Mode:** Compare two folders to find files that are common to both, based on a combination of criteria.
- **Find Duplicates Mode:** Analyze a single folder to find files that are duplicates of each other.
- **Unified "Compare" Action:** The main action button is always labeled "Compare" for a consistent user experience. The application internally handles whether to run a comparison or a duplicate-finding operation based on the selected mode.
- **Flexible & Robust Comparison:**
  - Compare by: File Name, Modification Date, File Size, and File Content (using MD5 hash).
  - The comparison logic is robust. If metadata for a specific file cannot be retrieved (e.g., due to a permission error), it is gracefully handled as a non-match for that criterion without crashing the program.
- **Project-Based Workflow:**
  - Create new projects, save, and load existing projects (`.cfp` files).
  - The application mode ("compare" or "duplicates"), folder paths, and comparison settings are all saved in the project.
  - File structures are "built" and saved to the project, which includes a tree of all files and folders.
- **Metadata Persistence:**
  - When a comparison is run, the calculated metadata is automatically saved back into the project file for each file.
  - The metadata is stored with specific keys, for example: `{"compare_size": 12345, "compare_content_md5": "...", "histogram_method": "Correlation"}`.
  - This avoids recalculating metadata on subsequent operations.
  - Rebuilding the file structure for one folder does not erase the data for the other folder in the project.

## File Structure

The project is organized into several key files and directories:

- **`main.py`**: The main entry point of the application. It initializes and runs the Tkinter app.

- **`ui.py`**: Contains the `FolderComparisonApp` class, which is responsible for creating and managing the entire GUI. It handles user interactions, manages the application state (like folder paths, app mode, and file structures), and orchestrates calls to the business logic.

- **`logic.py`**: Contains the core business logic that is independent of the UI. The `build_folder_structure` function recursively scans a directory and builds a tree of file and folder nodes.

- **`models.py`**: Defines the data models for the application.
  - `FileNode`: Represents a file. It includes a `metadata` dictionary to store arbitrary data from comparisons.

- **`strategies/`**: This directory contains the different comparison strategies.
  - **`find_common_strategy.py`**: Orchestrates the comparison of two folders. It returns the calculated metadata to the UI for saving.
  - **`compare_by_*.py`**: Individual, robust strategies that each implement a specific comparison logic (e.g., `compare_by_size.py`). They safely handle cases where metadata might be missing.
  - **`utils.py`**: Contains utility functions. `flatten_structure` is responsible for robustly generating all the metadata based on the selected UI options, handling potential `OSError` exceptions.

## How It Works

1.  **Project Creation/Loading:** The user starts a new project or loads a `.cfp` file. This file contains all settings, including the application mode.
2.  **Folder Selection & Building:** The user selects a folder and clicks "Build". This scans the folder and saves the file/folder structure into the project file.
3.  **Running the "Compare" Action:**
    - The user selects comparison options (e.g., "Size", "Content (MD5 Hash)").
    - When the "Compare" button is clicked, the application runs the appropriate logic based on the current mode.
    - The `flatten_structure` utility robustly generates metadata for each file.
    - The `find_common_strategy` uses this metadata to find matches, with individual comparison strategies safely ignoring files with missing data.
    - **Crucially, the newly calculated metadata is then saved back to the `FileNode` objects in the main application state, and the entire project is saved to the `.cfp` file.**
    - The results are displayed in the results list.
