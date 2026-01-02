# Technical README for the Folder Comparison Tool

## Introduction

Welcome, developer! This document provides a deep dive into the technical architecture and implementation of the Folder Comparison Tool. 

The project is currently undergoing a phased refactoring to move from a tightly coupled MVC-like structure to a more robust, SOLID-compliant architecture based on **Clean Architecture** principles and **Dependency Inversion**.

### Core Technologies

-   **Language:** Python 3
-   **GUI:** Tkinter (via the standard library)
-   **Data Persistence:** SQLite (for project files with a custom `.cfp-db` extension)
-   **Image Analysis:**
    -   Pillow for basic image handling and histogram generation.
    -   `llama-cpp-python` for advanced, AI-powered image similarity analysis.
-   **Architecture:** Moving towards Clean Architecture with strong use of Interfaces and Repositories.

---

## High-Level Architecture (Refactored)

The application is organized into layers to ensure separation of concerns and testability.

### 1. Abstraction Layer (`src/interfaces/`)
This layer defines the contracts that components must follow. It enables **Dependency Inversion (DIP)** so that high-level logic (Controller) does not depend on low-level details (UI, Database).
-   **`IView`**: Abstract interface for the UI. Defines methods like `update_status` and `root` access.
-   **`IFileRepository`**: Abstract interface for data access. Defines how to fetch files, sources, and perform deletions.
-   **`IComparisonStrategy` / `IMetadataCalculator`**: Formalized interfaces for the strategy pattern.

### 2. Domain Layer (`src/domain/`)
Contains immutable Value Objects that represent the system's core data.
-   **`FileInfo`**: A dataclass representing a file and its metadata (hashes, size, etc.).
-   **`ComparisonOptions`**: A dataclass that encapsulates all user selections from the UI.

### 3. Data Access Layer (`src/repositories/`)
Encapsulates all database-specific logic.
-   **`SQLiteRepository`**: The concrete implementation of `IFileRepository`. It uses the `database.py` module to interact with SQLite.

### 4. Controller (`src/controller.py`)
The business logic orchestrator. 
-   It no longer depends on the concrete `FolderComparisonApp`. Instead, it works with the `IView` interface.
-   It uses the `ProjectManager` and `SQLiteRepository` to manage data.
-   All internal data flow uses `FileInfo` and `ComparisonOptions` rather than raw dictionaries.

### 5. View Layer (`src/ui.py`)
The Tkinter-based GUI implementation.
-   Implements the `IView` interface.
-   Is injected into the Controller at startup.

---

## Project and Data Flow

### 1. Project Management
The `ProjectManager` handles creating and loading projects. When a project is active, it initializes a `SQLiteRepository` instance in the Controller, ensuring the data layer is always correctly pointing to the current project file.

### 2. Metadata Indexing (The "Build" Process)
1.  **UI:** User clicks "Build".
2.  **Controller:** Triggers `build_folders()`.
3.  **Logic (`logic.py`):** Scans the filesystem and syncs with the database via `database.py`.
4.  **Repository:** Provides a clean way to query the newly indexed files.

### 3. Comparison & Duplicate Finding
1.  **Options:** The UI state is gathered into a `ComparisonOptions` domain object.
2.  **Calculation:** `utils.calculate_metadata_db` uses this object to determine which metadata (MD5, LLM, etc.) needs to be computed.
3.  **Execution:** The `find_duplicates_strategy` runs queries against the repository and filters results.
4.  **Display:** The results are passed to the `IView` implementation for rendering in the Treeview.

---

## The Strategy Pattern

The application uses the Strategy Pattern for its comparison logic.

### Calculators & Comparators
-   **Calculators** (`strategies/<type>/calculator.py`): Compute metadata (e.g., `MD5Calculator`).
-   **Comparators** (`strategies/<type>/comparator.py`): Compare two files based on specific criteria.

### How to Add a New Comparison Strategy

1.  **Interface implementation**: Create a Calculator and Comparator (implementing `IMetadataCalculator` and `IComparisonStrategy`).
2.  **Database update**: Add necessary columns to the `file_metadata` table in `database.py`.
3.  **Domain model**: Update `ComparisonOptions` and `FileInfo` to include the new field.
4.  **UI/Controller**: Add the corresponding UI toggle and Link it to a variable in the controller.

---

## The AI Engine (LLM-Based Comparison)

The `LlavaEmbeddingEngine` (`ai_engine/engine.py`) provides semantic image comparison.
1.  **Initialization**: Loaded in a background thread to avoid UI lag.
2.  **Embeddings**: 512-dimension vectors stored as `BLOB` in `file_metadata`.
3.  **Similarity**: Uses **Cosine Similarity** to match images. Threshold is configurable via the UI.

---

## Design Principles in Practice

-   **Single Responsibility Principle (SRP)**: Logic is being moved out of the UI and Controller into specialized services and repositories.
-   **Open/Closed Principle (OCP)**: The Strategy Pattern allows adding new comparison methods without modifying core execution logic.
-   **Dependency Inversion Principle (DIP)**: High-level modules use interfaces to communicate with low-level implementations.
