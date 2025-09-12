# Tests

This directory contains the unit tests for the application.

## Running Tests

To run all tests, execute the following command from the root directory of the project:

```bash
python -m unittest discover tests
```

## Individual Tests

### `test_find_duplicates_by_name_and_size.py`

This test verifies the duplicate finding functionality based on file name and size.

*   **Target Folder**: `tests/imgs/` (including subdirectories)
*   **Comparison Criteria**:
    *   File Name
    *   File Size
*   **Expected Outcome**:
    *   The test expects to find exactly one group of duplicate files.
    *   This group should contain two files, both named `8151.jpg`.
    *   One of these files is located in the root of `tests/imgs/`, and the other is in the `tests/imgs/subfolder/` directory.
    *   The test asserts that both files have the same name and size, and are correctly identified as a duplicate set.

This test was created to verify a specific user request and is temporary. It will be deleted after the explanation is provided.
