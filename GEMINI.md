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

This application allows users to save and load "projects". It supports two project file formats:
- **`.cfp`**: A JSON-based format for smaller projects.
- **`.cfp-db`**: A SQLite-based format for larger projects, offering better performance and scalability.

The application has two primary modes:
1.  **Compare Folders**: Finds files that are common to two different folders.
2.  **Find Duplicates**: Finds duplicate files within a single folder.

## 3. Architecture

The application follows a separation of concerns between the UI, business logic, data models, and comparison strategies.

-   **`ui.py` (UI & Orchestration)**: This is the core of the application. The `FolderComparisonApp` class manages the Tkinter GUI, application state (folder paths, selected options), and orchestrates the calls to the business logic. It handles all user interactions, project saving/loading, and displaying results. **Most changes to application flow will likely involve this file.**

-   **`database.py` (Database Logic)**: This module handles all SQLite-related operations, including creating the database schema, inserting and updating file information, and retrieving data for comparison.

-   **`logic.py` (Initial Structure Building)**: This module is responsible for the initial scan of a folder. 
    - For JSON-based projects, `build_folder_structure` recursively walks a directory path and creates a tree of `FileNode` and `FolderNode` objects.
    - For SQLite-based projects, `build_folder_structure_db` scans a directory and inserts file information directly into the database.

-   **`models.py` (Data Models)**: Defines the core data structures for JSON-based projects:
    -   `FileSystemNode`: A base class for files and folders.
    -   `FileNode`: Represents a single file and contains a `metadata` dictionary.
    -   `FolderNode`: Represents a folder and contains a list of other nodes (`content`).
    -   These objects have a `to_dict()` method for JSON serialization into the `.cfp` project file.

-   **`strategies/` (Comparison & Duplicate Logic)**: This directory contains the "brains" of the comparison and duplicate-finding operations. **This is where the core algorithms are implemented.**
        -   **`strategies/calculators/`**: This sub-package contains modular "calculators" for metadata. Each calculator is responsible for a single piece of metadata (e.g., `MD5Calculator`, `HistogramCalculator`). This makes the system more extensible.
    -   **`utils.py`**: A crucial file containing functions to calculate metadata. 
        - `flatten_structure` traverses the `FileNode` tree for JSON projects, using the modular calculators to gather metadata. It returns a flat dictionary of file information, similar to `calculate_metadata_db`.
        - `calculate_metadata_db` reads from and updates the SQLite database for `.cfp-db` projects.
    -   **`find_common_strategy.py`**: Orchestrates the logic for the "Compare Folders" mode. It uses the `StrategyRegistry` to dynamically dispatch to the appropriate comparison strategies based on user options.
    -   **`find_duplicates_strategy.py`**: Orchestrates the logic for the "Find Duplicates" mode. It uses a more complex, two-phase approach:
        1.  **Grouping**: Uses `key_by_*.py` modules to group files into buckets based on shared properties (e.g., all files with the same size).
        2.  **Pairwise Comparison**: If necessary (e.g., for histograms), it performs detailed comparisons *within* the groups.
    -   **`compare_by_*.py`**: These modules contain the concrete implementations of the `BaseComparisonStrategy`.
    -   **`strategy_registry.py`**: This module automatically discovers and registers all available comparison strategies, making the system easily extensible.

## 4.5. LLM Similarity Engine

The application includes a powerful but resource-intensive image similarity feature based on the LLaVA (Large Language and Vision Assistant) model.

### How It Works

1.  **Engine Initialization**: On startup, the application looks for the required LLaVA model files in the `models/` directory. If found, it loads the model into memory.
2.  **Embedding Generation**: When the "LLM Content" option is selected, the application uses the LLaVA model to generate a high-dimensional vector (an "embedding") for each image. This embedding represents the semantic content of the image.
3.  **Metadata Persistence**: These embeddings are stored in the project's `.cfp` or `.cfp-db` file, so they only need to be generated once per image.
4.  **Comparison**: The application then calculates the cosine similarity between the embeddings of different images to determine how similar they are.

### Requirements

-   **Model Files**: You must download the correct GGUF model files and place them in the `models/` directory. See the `models/README.md` file for detailed instructions.
-   **RAM**: A minimum of 16 GB of system RAM is strongly recommended. The model itself requires about 5 GB of memory.
-   **Performance**: Embedding generation is very slow on CPU. For reasonable performance, a modern GPU (NVIDIA or Apple Silicon) is highly recommended. This requires compiling the `llama-cpp-python` dependency with the correct flags (e.g., `CMAKE_ARGS="-DGGML_CUDA=on"`).

### Usage

-   Enable the "LLM Content" checkbox in the UI.
-   Be aware that the metadata calculation step (`run_action`) will be significantly slower when this option is enabled.
-   Currently, the similarity threshold for the LLM comparison reuses the "Histogram Threshold" value from the UI.

## 5. How to Contribute

We welcome contributions to this project. To contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix  ([YYYYMM]/feature/[description]).
3.  Make your changes and commit them with a clear and descriptive commit message.
4.  Push your changes to your fork (always ask befor push).

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

## 10. UI Modifications

- Increased the default size of the 'New Project' window for better usability.

## 11. Improvements

-   **Database Schema Alignment**: Modified `logic.py` to correctly store the file's directory path in the `path` column of the `files` table, aligning with the database schema and separating it from the filename stored in the `name` column. This resolves a previous mismatch where `logic.py` was attempting to insert into a non-existent `relative_path` column.
-   **Database Normalization**: Extracted `size`, `modified_date`, `md5`, `histogram`, and `llm_embedding` from the `files` table into a new `file_metadata` table.
    -   `database.py`: Modified `create_tables` to define the new `file_metadata` table and remove these columns from `files`. Updated `insert_file_node` to insert into both `files` and `file_metadata`.
    -   `logic.py`: Modified `build_folder_structure_db` to perform individual UPSERT operations for `files` and `file_metadata` due to the inability of `executemany` to return `lastrowid` for linking.
-   **Database Query Fix**: Corrected a bug in `logic.py` where the database query to check for existing files was only checking the folder path and not the filename. This caused only one file per folder to be recorded. The query has been updated to include the filename, ensuring all files are correctly processed.
-   **Duplicate Finding Fix**: Corrected a bug in `find_duplicates_strategy.py` where file paths from the database (strings) were not being converted to `pathlib.Path` objects, causing the duplicate detection to fail.