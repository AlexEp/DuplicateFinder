# Folder Comparison and Duplicate Finder Tool

This tool provides a graphical user interface (GUI) to compare two folders or find duplicate files within a single folder. It is built using Python's Tkinter library.

The application supports various comparison strategies and can be extended with new ones. It uses a project-based approach, allowing users to save their settings and folder metadata for later use.

## Features

- **Compare Mode:** Compare two folders to find files that are common to both, based on a combination of criteria.
- **Find Duplicates Mode:** Analyze a single folder to find files that are duplicates of each other.
- **Flexible Comparison Criteria:**
  - File Name
  - Modification Date
  - File Size
  - File Content (using MD5 hash)
  - Image Similarity (using histogram analysis)
- **Project-Based Workflow:**
  - Create new projects.
  - Save and load existing projects (`.cfp` files).
  - Folder paths and comparison settings are saved in the project.
  - File structures are "built" and saved to the project, which includes a tree of all files and folders.
- **Metadata Persistence:**
  - When a comparison is run, the calculated metadata (like file size, MD5 hash, etc.) is automatically saved back into the project file for each file.
  - This avoids recalculating metadata on subsequent operations and allows for more complex analysis in the future.
  - Rebuilding the file structure for one folder does not erase the data for the other folder in the project.

## File Structure

The project is organized into several key files and directories:

- **`main.py`**: The main entry point of the application. It initializes and runs the Tkinter app.

- **`ui.py`**: Contains the `FolderComparisonApp` class, which is responsible for creating and managing the entire GUI. It handles user interactions, manages the application state (like folder paths and file structures), and orchestrates calls to the business logic.

- **`logic.py`**: Contains the core business logic that is independent of the UI. The `build_folder_structure` function recursively scans a directory and builds a tree of file and folder nodes.

- **`models.py`**: Defines the data models for the application.
  - `FileSystemNode`: A base class for files and folders.
  - `FileNode`: Represents a file. It now includes a `metadata` dictionary to store arbitrary data from comparisons (e.g., size, hash).
  - `FolderNode`: Represents a folder and contains a list of other `FileNode` and `FolderNode` objects.

- **`strategies/`**: This directory contains the different comparison and keying strategies used by the application. This modular approach allows for easy extension.
  - **`__init__.py`**: Makes the directory a Python package.
  - **`find_common_strategy.py`**: Orchestrates the comparison of two folders by using the other, more specific comparison strategies. It now returns the calculated metadata to the UI.
  - **`find_duplicates_strategy.py`**: Orchestrates the process of finding duplicate files.
  - **`compare_by_*.py`**: Individual files that each implement a specific comparison logic (e.g., `compare_by_size.py`, `compare_by_content_md5.py`).
  - **`key_by_*.py`**: Individual files that provide a "key" for a file, used for grouping in the duplicate finding mode.
  - **`utils.py`**: Contains utility functions used by the strategies, such as `calculate_md5` and `flatten_structure`.

## How It Works

1.  **Project Creation:** The user starts by creating a new project or loading an existing one. A project file (`.cfp`) is a JSON file that stores all settings and metadata.
2.  **Folder Selection:** The user selects one or two folders to work with. These paths are saved to the project.
3.  **Building Metadata:** The user clicks the "Build" button for a folder. This process:
    - Scans the folder recursively.
    - Creates a tree structure of `FileNode` and `FolderNode` objects.
    - Saves this file structure into the project file.
4.  **Running an Action (Compare/Find Duplicates):**
    - The user selects comparison options from the UI.
    - When "Compare" is clicked, the application uses the `find_common_strategy`.
    - This strategy calculates the necessary metadata (e.g., file size) for each file based on the selected options.
    - It compares the files and identifies matches.
    - **Crucially, the newly calculated metadata is then saved back to the `FileNode` objects in the main application state, and the entire project is saved to the `.cfp` file.**
    - The results are displayed in the results list.
