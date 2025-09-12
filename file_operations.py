import os
import shutil
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import logging
import database
from models import FileNode, FolderNode

logger = logging.getLogger(__name__)

def _remove_node_from_structure(structure, fullpath):
    """Recursively removes a node from the structure by its fullpath."""
    for i, node in enumerate(structure):
        if isinstance(node, FileNode) and str(node.fullpath) == str(fullpath):
            del structure[i]
            return True
        elif isinstance(node, FolderNode):
            if _remove_node_from_structure(node.content, fullpath):
                return True
    return False

def move_file(controller, base_path_str, relative_path_str, dest_path_str, results_tree, iid, update_status_callback):
    if not base_path_str or not dest_path_str:
        logger.warning("Move file cancelled: source or destination folder path is not set.")
        messagebox.showwarning("Warning", "Source or destination folder path is not set.")
        return

    try:
        source_path = Path(base_path_str) / relative_path_str
        dest_path = Path(dest_path_str) / source_path.name  # move to folder, keep original name
        logger.info(f"Attempting to move file from '{source_path}' to '{dest_path}'.")

        if not source_path.is_file():
            logger.error(f"Move failed: source file does not exist at '{source_path}'.")
            messagebox.showerror("Error", f"Source file does not exist:\n{source_path}")
            return

        if dest_path.exists():
            if not messagebox.askyesno("Confirm Overwrite", f"Destination file already exists. Overwrite?\n\n{dest_path}"):
                logger.info("Move cancelled by user (overwrite confirmation).")
                return

        confirm = messagebox.askyesno(
            "Confirm Move",
            f"Are you sure you want to move this file?\n\nFrom: {source_path}\nTo: {dest_path}"
        )
        if not confirm:
            logger.info("Move cancelled by user (move confirmation).")
            return

        shutil.move(source_path, dest_path)
        results_tree.delete(iid)

        # Update data
        if controller.project_manager.current_project_path.endswith(".cfp-db"):
            conn = database.get_db_connection(controller.project_manager.current_project_path)
            path, name = os.path.split(relative_path_str)
            database.delete_file_by_path(conn, path, name)
            conn.close()
        else:
            if controller.folder1_path.get() == base_path_str:
                _remove_node_from_structure(controller.folder1_structure, source_path)
            elif controller.folder2_path.get() == base_path_str:
                _remove_node_from_structure(controller.folder2_structure, source_path)

        update_status_callback(f"Moved: {source_path.name} to {dest_path}")
        logger.info(f"Successfully moved file from '{source_path}' to '{dest_path}'.")

    except Exception as e:
        logger.error(f"Failed to move file from '{source_path}' to '{dest_path}'.", exc_info=True)
        messagebox.showerror("Error", f"Could not move file:\n{e}")

def delete_file(controller, base_path_str, relative_path_str, results_tree, iid, update_status_callback):
    if not base_path_str:
        logger.warning(f"Delete file cancelled: base path is not set.")
        messagebox.showwarning("Warning", "Base path is not set.")
        return

    try:
        full_path = Path(base_path_str) / relative_path_str
        logger.info(f"Attempting to delete file: {full_path}")
        if not full_path.is_file():
            logger.error(f"Delete failed: file does not exist at '{full_path}'.")
            messagebox.showerror("Error", f"File does not exist:\n{full_path}")
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete this file?\n\n{full_path}"
        )
        if not confirm:
            logger.info(f"Deletion cancelled by user for file: {full_path}")
            return

        os.remove(full_path)
        results_tree.delete(iid)

        # Update data
        if controller.project_manager.current_project_path.endswith(".cfp-db"):
            conn = database.get_db_connection(controller.project_manager.current_project_path)
            path, name = os.path.split(relative_path_str)
            database.delete_file_by_path(conn, path, name)
            conn.close()
        else:
            if controller.folder1_path.get() == base_path_str:
                _remove_node_from_structure(controller.folder1_structure, full_path)
            elif controller.folder2_path.get() == base_path_str:
                _remove_node_from_structure(controller.folder2_structure, full_path)

        update_status_callback(f"Deleted: {full_path}")
        logger.info(f"Successfully deleted file: {full_path}")

    except Exception as e:
        logger.error(f"Failed to delete file: {full_path}", exc_info=True)
        messagebox.showerror("Error", f"Could not delete file:\n{e}")

def open_containing_folder(base_path_str, relative_path_str):
    if not base_path_str:
        logger.warning(f"Open folder cancelled: base path is not set.")
        messagebox.showwarning("Warning", "Base path is not set.")
        return

    try:
        full_path = Path(base_path_str) / relative_path_str
        dir_path = full_path.parent
        logger.info(f"Opening containing folder for: {full_path}")

        if not dir_path.is_dir():
            logger.error(f"Open folder failed: directory does not exist at '{dir_path}'.")
            messagebox.showerror("Error", f"Directory does not exist:\n{dir_path}")
            return

        if sys.platform == "win32":
            os.startfile(dir_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(dir_path)])
        else:
            subprocess.Popen(["xdg-open", str(dir_path)])
    except Exception as e:
        logger.error(f"Failed to open containing folder for: {full_path}", exc_info=True)
        messagebox.showerror("Error", f"Could not open folder:\n{e}")
