# Gemini Development Guide

This document provides guidance for Gemini agents working on this codebase.

## 1. Getting Started

This is a Python desktop application built with Tkinter for comparing folders and finding duplicate files. To get started, you will need to have Python 3 and Tkinter installed on your system.

To run the application, execute the following command from the root directory of the project:

```bash
python main.py
```

To install the required dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## 2. Project Overview

This application allows users to save and load "projects" (`.cfp` files), which store folder paths, comparison settings, and file metadata.

The application has two primary modes:
1.  **Compare Folders**: Finds files that are common to two different folders.
2.  **Find Duplicates**: Finds duplicate files within a single folder.

## 3. Architecture

The application follows a separation of concerns between the UI, business logic, data models, and comparison strategies.

-   **`ui.py` (UI & Orchestration)**: This is the core of the application. The `FolderComparisonApp` class manages the Tkinter GUI, application state (folder paths, selected options), and orchestrates the calls to the business logic. It handles all user interactions, project saving/loading, and displaying results. **Most changes to application flow will likely involve this file.**

-   **`logic.py` (Initial Structure Building)**: This module is responsible for the initial scan of a folder. The `build_folder_structure` function recursively walks a directory path and creates a tree of `FileNode` and `FolderNode` objects. This is a one-time operation per folder, and the result is saved in the project file.

-   **`models.py` (Data Models)**: Defines the core data structures:
    -   `FileSystemNode`: A base class for files and folders.
    -   `FileNode`: Represents a single file and contains a `metadata` dictionary.
    -   `FolderNode`: Represents a folder and contains a list of other nodes (`content`).
    -   These objects have a `to_dict()` method for JSON serialization into the `.cfp` project file.

-   **`strategies/` (Comparison & Duplicate Logic)**: This directory contains the "brains" of the comparison and duplicate-finding operations. **This is where the core algorithms are implemented.**
    -   **`utils.py`**: A crucial file containing the `flatten_structure` function. This function traverses the built `FileNode` tree and calculates the actual metadata (size, date, MD5 hash, image histogram) based on the user's selected options. **This is where file I/O and CPU-intensive calculations happen.**
    -   **`find_common_strategy.py`**: Orchestrates the logic for the "Compare Folders" mode. It takes the metadata for two folders and runs a series of simple, one-to-one comparisons.
    -   **`find_duplicates_strategy.py`**: Orchestrates the logic for the "Find Duplicates" mode. It uses a more complex, two-phase approach:
        1.  **Grouping**: Uses `key_by_*.py` modules to group files into buckets based on shared properties (e.g., all files with the same size).
        2.  **Pairwise Comparison**: If necessary (e.g., for histograms), it performs detailed comparisons *within* the groups.
    -   **`compare_by_*.py`**: These are the individual, granular comparison functions (e.g., `compare_by_size.py`). They compare two files based on a single criterion.
    -   **`key_by_*.py`**: These modules generate a "key" for a single file (e.g., `key_by_size.py` returns the file's size). This key is used for the grouping phase in the duplicate-finding strategy.

## 4. The Metadata-First Workflow

It is critical to understand the application's workflow to work on it effectively:

1.  **Build**: The user selects a folder and clicks "Build". `logic.build_folder_structure` is called to create a basic tree of file and folder objects. This structure is saved to the project file. **No expensive metadata is calculated at this stage.**
2.  **Compare Action**: The user selects comparison options (e.g., "Size", "Content (MD5)") and clicks the main "Compare" button.
3.  **Metadata Calculation**: The `run_action` method in `ui.py` calls `strategies.utils.flatten_structure`. This function iterates through the previously built structure and **calculates the required metadata** (e.g., it now runs the MD5 hash calculation).
4.  **Metadata Persistence**: The newly calculated metadata is immediately saved back into the project file (`.cfp`). This ensures that if the user runs the same comparison again, the metadata does not need to be recalculated.
5.  **Strategy Execution**: The metadata is passed to the appropriate strategy (`find_common_strategy` or `find_duplicates_strategy`) to get the final results.

**When adding a new comparison criterion, you must:**
1.  Add a checkbox or other UI element in `ui.py`.
2.  In `strategies/utils.py`, add the logic to `flatten_structure` to calculate the new metadata when the option is selected.
3.  Create a new `compare_by_your_new_criterion.py` file in `strategies/`.
4.  If it can be used for finding duplicates, also create a `key_by_your_new_criterion.py` file.
5.  Integrate the new strategy module into `find_common_strategy.py` and/or `find_duplicates_strategy.py`.

## 5. How to Contribute

We welcome contributions to this project. To contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with a clear and descriptive commit message.
4.  Push your changes to your fork.
5.  Create a pull request to the main repository.

## 6. Code Style

This project follows the PEP 8 style guide for Python code. Please ensure that your code adheres to this style guide.

## 7. Testing

The project has a `tests/` directory containing unit tests. To run the tests, use Python's built-in `unittest` module from the root directory of the project.

```bash
python -m unittest discover tests
```

Before submitting any changes, you **must** run the tests to ensure that you have not introduced any regressions. If you add new logic, you should add corresponding tests.

## 8. Deployment

This application is designed to be run from the source code. There is no separate deployment process.

## 9. License

This project is licensed under the MIT License. See the `LICENSE` file for more details.