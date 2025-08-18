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
  - When the "Compare" button is pressed, the application calculates metadata for all files based on the selected options and immediately saves it to the project file. This happens for both "Compare Folders" and "Find Duplicates" modes.
  - The metadata is stored with specific keys, for example: `{"compare_size": 12345, "compare_content_md5": "..."}`.
  - This avoids recalculating metadata on subsequent operations.

## File Structure

The project is organized into several key files and directories:

- **`main.py`**: The main entry point of the application.
- **`ui.py`**: Contains the `FolderComparisonApp` class, which manages the entire GUI, application state, and orchestration of the core logic.
- **`logic.py`**: Contains the UI-independent logic for building the folder structure.
- **`models.py`**: Defines the data models, including the `FileNode` which holds file-specific metadata.
- **`strategies/`**: This directory contains the different comparison strategies.
  - `utils.py`: Contains robust utility functions for generating file metadata.
  - `find_common_strategy.py` & `find_duplicates_strategy.py`: Orchestrate the logic for the two primary modes, now consuming pre-calculated metadata.
  - `compare_by_*.py`: Individual, robust strategies for specific comparisons.
- **`tests/`**: Contains unit tests for the application's logic.
  - `test_strategies.py`: Contains tests to verify the robustness and correctness of the comparison strategies.

## How It Works

1.  **Project Creation/Loading:** The user starts a new project or loads a `.cfp` file. This file contains all settings, including the application mode.
2.  **Folder Selection & Building:** The user selects a folder and clicks "Build". This scans the folder and saves the basic file/folder structure into the project file.
3.  **Running the "Compare" Action:**
    - The user selects comparison options (e.g., "Size", "Content (MD5 Hash)").
    - When the "Compare" button is clicked, the application first calculates all the selected metadata for every file in the loaded folder structures and saves this information to the project file.
    - Then, based on the current mode ("compare" or "duplicates"), it passes this metadata to the appropriate strategy to find matches or duplicate sets.
    - The results are displayed in the results list.
