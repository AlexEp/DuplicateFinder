# Technical README for the Folder Comparison Tool

## Introduction

Welcome, developer! This document provides a deep dive into the technical architecture and implementation of the Folder Comparison Tool. The goal is to give you a comprehensive understanding of the codebase, enabling you to contribute effectively.

This application is a desktop utility for finding duplicate files within a folder or comparing multiple folders to find common files. It is built with a focus on robustness, performance, and extensibility.

### Core Technologies

-   **Language:** Python 3
-   **GUI:** Tkinter (via the standard library)
-   **Data Persistence:** SQLite (for project files with a custom `.cfp-db` extension)
-   **Image Analysis:**
    -   Pillow for basic image handling and histogram generation.
    -   `llama-cpp-python` for advanced, AI-powered image similarity analysis using a LLaVA (Large Language and Vision Assistant) model.
-   **Architecture:** A Model-View-Controller (MVC)-like pattern.
-   **Extensibility:** A strategy pattern allows for the easy addition of new comparison methods.

## High-Level Architecture

The application follows a Model-View-Controller (MVC) like pattern to separate concerns, making the codebase easier to manage and extend.

-   **`main.py`**: The main entry point of the application. Its sole responsibility is to initialize the logger, instantiate the View (`FolderComparisonApp`) and the Controller (`AppController`), and start the Tkinter main event loop.

-   **View (`ui.py`)**: This is the entire graphical user interface (GUI), built using Tkinter.
    -   It is responsible for creating and arranging all widgets (buttons, lists, checkboxes, etc.).
    -   It holds references to Tkinter variables (e.g., `tk.StringVar`, `tk.BooleanVar`) that represent the state of the UI controls.
    -   It binds user actions (e.g., button clicks, menu selections) to methods in the `AppController`.
    -   It is designed to be "dumb" - it knows how to display things and capture user input, but it does not contain any business logic.

-   **Controller (`controller.py`)**: This is the central nervous system of the application.
    -   It connects the View and the Model.
    -   It holds the application's state (e.g., the current comparison settings).
    -   It contains the methods that are triggered by user actions in the View (e.g., `run_action`, `build_active_folders`).
    -   It orchestrates complex operations by calling functions from the `logic` and `database` modules.
    -   It uses a `TaskRunner` utility to execute long-running operations (like scanning folders or running comparisons) in background threads, preventing the UI from freezing.

-   **Model (Various Files)**: The "Model" is not a single class but is composed of several components that manage the application's data and business rules.
    -   **`database.py`**: Handles all direct interactions with the SQLite database. It contains functions for creating the schema, reading/writing settings, and querying file data. This is the only part of the application that should execute SQL queries.
    -   **`logic.py`**: Contains the core, UI-independent business logic. For example, the `build_folder_structure_db` function (which scans the filesystem) and the `run_comparison` function (which implements the efficient matching algorithm) reside here.
    -   **`models.py`**: Defines the data classes (`FileNode`, `FolderNode`) used to represent file system objects in memory. These are primarily a holdover from a previous, non-database design but are still used in some parts of the code.
    -   **`project_manager.py`**: Manages the lifecycle of a project, including creating, loading, and saving the `.cfp-db` files.

## Project and Data Flow

Understanding the flow of data from user action to final result is key to working with this codebase. The application is stateful and revolves around a central project file.

### 1. Project Creation

1.  **User Action:** The user clicks "File" -> "New Project".
2.  **UI (`ui.py`):** A dialog appears asking the user to add one or more root folders for the project.
3.  **Controller/Project Manager:** Upon saving, the `ProjectManager` creates a new SQLite database file (e.g., `MyProject.cfp-db`).
4.  **Database (`database.py`):**
    -   The `create_tables` function is called to set up the initial database schema (`project_settings`, `sources`, `files`, `file_metadata`).
    -   The selected root folders are saved into the `sources` table.
    -   The main application window is now enabled and linked to this project file.

### 2. The "Build" Process (Metadata Indexing)

This is a critical, read-only operation that scans the filesystem.

1.  **User Action:** The user clicks the "Build" button.
2.  **Controller (`controller.py`):** The `build_active_folders` method is called. It iterates through the source folders stored in the project.
3.  **Logic (`logic.py`):** For each folder, the `build_folder_structure_db` function is executed in a background thread.
    -   This function performs a full scan of the folder (and subfolders, if selected).
    -   It compares the files on disk with the records in the `files` table for that source.
    -   **Synchronization:**
        -   **New Files:** New records are inserted into the `files` table. Basic metadata (`size`, `modified_date`) is added to the `file_metadata` table.
        -   **Unchanged Files:** Their `last_seen` timestamp is updated.
        -   **Deleted Files:** Any file records in the database that were not "seen" during the scan are deleted.
    -   This process ensures that the database is an up-to-date reflection of the filesystem. No expensive metadata (like MD5 hashes) is calculated at this stage.

### 3. The "Compare" / "Find Duplicates" Action

This is where the heavy lifting happens.

1.  **User Action:** The user selects comparison options (e.g., "Size", "Content (MD5 Hash)") and clicks the main action button ("Compare Folders" or "Find Duplicates").
2.  **Controller (`controller.py`):** The `run_action` method is called.
3.  **Metadata Calculation (`strategies/utils.py` -> `calculate_metadata_db`):**
    -   This is the first step within the background task. The function gets a list of all files for the relevant sources from the database.
    -   It iterates through all registered **Calculators** (see Strategy Pattern section below).
    -   For each file, it checks if the corresponding metadata (e.g., `md5`) is missing from the database *and* if the user has ticked the corresponding comparison option.
    -   If both are true, it calls the `calculate` method of the specific calculator (e.g., `MD5Calculator.calculate()`), which computes the value (e.g., an MD5 hash).
    -   The newly calculated metadata is immediately saved to the `file_metadata` table in the database. This ensures that metadata is calculated only once.
4.  **Comparison (`logic.py` -> `run_comparison` or `strategies/find_duplicates_strategy.py`):**
    -   After all necessary metadata has been calculated and stored, the appropriate comparison function is called.
    -   It retrieves the file data, including all the required metadata, from the database.
    -   It then uses an efficient, hash-based approach to find matches. For each file, it creates a key (a tuple) from the selected metadata values (e.g., `(12345, 'd41d8cd98f00b204e9800998ecf8427e')`).
    -   Files with identical keys are grouped together as matches or duplicates.
5.  **View (`ui.py`):** The final list of matched groups is passed back to the main thread and displayed in the results `Treeview`.

## Database Schema

The `.cfp-db` project file is a standard SQLite database. The schema is defined in `database.py` and is designed to be normalized, separating file identity from its various metadata.

### `project_settings`
A simple key-value store for persisting UI settings and other project-level information.
-   `key` (TEXT, PRIMARY KEY): The name of the setting (e.g., `"compare_options"`).
-   `value` (TEXT): The value of the setting, typically stored as a JSON string.

### `sources`
Stores the absolute paths of the root folders included in the project.
-   `id` (INTEGER, PRIMARY KEY): A unique identifier for each source folder (e.g., 1, 2, 3...).
-   `path` (TEXT, UNIQUE): The full, absolute path to the folder (e.g., `C:/Users/Me/Pictures/Vacation2023`).

### `files`
This is the central table containing a record for every single file found within every source folder.
-   `id` (INTEGER, PRIMARY KEY): A unique identifier for each file record.
-   `folder_index` (INTEGER): A foreign key referencing `sources.id`. This tells us which root folder this file belongs to.
-   `path` (TEXT): The relative path of the file from its source folder's root.
-   `name` (TEXT): The name of the file including its extension (e.g., `image.jpg`).
-   `ext` (TEXT): The file extension (e.g., `.jpg`).
-   `last_seen` (REAL): A timestamp that is updated during the "Build" process. This is used to detect and remove records of deleted files.

### `file_metadata`
This table stores all the calculated metadata for files. It has a one-to-one relationship with the `files` table. This design avoids cluttering the main `files` table and allows for metadata to be added or updated without modifying the core file record.
-   `id` (INTEGER, PRIMARY KEY): The primary key for the metadata record itself.
-   `file_id` (INTEGER, UNIQUE): A foreign key referencing `files.id`.
-   `size` (INTEGER): The file size in bytes.
-   `modified_date` (REAL): The last modification timestamp of the file.
-   `md5` (TEXT): The MD5 hash of the file content.
-   `histogram` (TEXT): The image histogram data, stored as a JSON string.
-   `llm_embedding` (BLOB): The vector embedding generated by the LLaVA model, stored as a binary large object.

## The Strategy Pattern: Extending the Application

The application's most powerful feature for developers is its use of the Strategy Pattern, which allows new comparison methods to be added with minimal effort and without modifying the core application logic.

The system is built around two types of components: **Calculators** and **Comparators**.

-   **Calculators (`strategies/<type>/calculator.py`):** A calculator is responsible for computing a specific piece of metadata for a file (e.g., its MD5 hash) and knows which database column to store it in.
-   **Comparators (`strategies/<type>/comparator.py`):** A comparator defines what it means for two files to be "equal" based on a single criterion. It primarily serves to link a UI option to a database key.

### How it Works

1.  **Discovery:** On startup, `strategy_registry.discover_strategies()` scans the `strategies` directory for any modules containing `comparator` or `calculator` in their name and registers every valid class it finds.
2.  **Metadata Calculation:** When the user runs an action, `utils.calculate_metadata_db` iterates through all registered `Calculators`. If a calculator corresponds to a user-selected option, its `calculate()` method is called to generate the metadata, which is then stored in the database.
3.  **Comparison:** The main `logic.run_comparison` function gets the list of user-selected comparison strategies. It uses the `db_key` property from each strategy to build a composite key (a tuple) for each file. Files with identical composite keys are considered matches.

### How to Add a New Comparison Strategy

Let's say you want to add a new strategy to compare images based on their dimensions (width x height).

**Step 1: Create the Calculator**

Create a new file: `strategies/dimensions/calculator.py`

```python
from ..base_calculator import BaseCalculator
from PIL import Image
import json

class DimensionsCalculator(BaseCalculator):
    @property
    def db_key(self):
        # This MUST match a column in the file_metadata table.
        # You would need to add an 'image_dimensions' TEXT column first.
        return 'image_dimensions'

    def calculate(self, file_node, opts):
        # Check if the relevant UI option is ticked.
        # Let's assume the option key is 'compare_dimensions'.
        if opts.get('compare_dimensions'):
            try:
                with Image.open(file_node.fullpath) as img:
                    dimensions = {'width': img.width, 'height': img.height}
                    return json.dumps(dimensions)
            except Exception:
                # Not an image or corrupted file
                return None
        return None
```

**Step 2: Create the Comparator**

Create a new file: `strategies/dimensions/comparator.py`

```python
from ..base_comparison_strategy import BaseComparisonStrategy

class CompareByDimensions(BaseComparisonStrategy):
    @property
    def option_key(self):
        # This MUST match the variable name of a tk.BooleanVar in the controller
        # and the key checked in the calculator.
        return 'compare_dimensions'

    @property
    def db_key(self):
        # This MUST match the db_key in the calculator.
        return 'image_dimensions'

    def compare(self, file1_info, file2_info, opts=None):
        # This method is less critical for the main comparison logic
        # but should be implemented for completeness.
        dim1 = file1_info.get(self.db_key)
        dim2 = file2_info.get(self.db_key)
        if dim1 and dim2:
            return dim1 == dim2
        return False
```

**Step 3: Update the Database Schema**

In `database.py`, add the new column to the `file_metadata` table:

```sql
CREATE TABLE IF NOT EXISTS file_metadata (
    ...
    md5 TEXT,
    histogram TEXT,
    llm_embedding BLOB,
    image_dimensions TEXT, -- Add this line
    FOREIGN KEY (file_id) REFERENCES files(id)
)
```

**Step 4: Update the UI and Controller**

1.  **Controller (`controller.py`):** Add a new `tk.BooleanVar` for the option:
    `self.compare_dimensions = tk.BooleanVar(value=False)`
2.  **UI (`ui.py`):** Add a new `tk.Checkbutton` in the `create_widgets` method, linking it to the new variable:
    `tk.Checkbutton(match_frame, text="Dimensions", variable=self.compare_dimensions)`

That's it! The application will automatically discover your new strategy and incorporate it into the comparison logic.

## The AI Engine (LLM-Based Comparison)

For advanced image similarity, the application can use a local LLaVA (Large Language and Vision Assistant) model to generate "semantic embeddings" for images.

### How it Works

1.  **Engine (`ai_engine/engine.py`):** The `LlavaEmbeddingEngine` class is responsible for this process.
    -   **Initialization:** When first needed, the controller loads this engine in a background thread. This is a heavy operation, as it loads a multi-gigabyte LLaVA model (`.gguf`) and a corresponding CLIP model (`.mmproj`) into memory using the `llama-cpp-python` library.
    -   **Embedding Generation:** The `get_image_embedding` method takes an image file, processes it with the CLIP model, and feeds the result to the LLaVA model. The output is a vector (a list of numbers, e.g., `[0.12, -0.5, 0.88, ...]`) that numerically represents the semantic content of the image. This vector is the "embedding."

2.  **Storage:** The generated embedding is stored as a `BLOB` in the `llm_embedding` column of the `file_metadata` table.

3.  **Comparison:** The corresponding `LLMComparator` (not detailed here, but present in the `strategies` folder) does not compare embeddings for exact equality. Instead, it calculates the **cosine similarity** between two embedding vectors. This calculation results in a score between -1.0 and 1.0, where 1.0 means the images are semantically identical. If this score is above a user-defined threshold (e.g., 0.85), the images are considered a match.

This technique allows the application to find images that are conceptually similar (e.g., two different photos of a cat in a garden) even if their pixel data is completely different.
