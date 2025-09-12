import tkinter as tk
from tkinter import messagebox
import logging
from pathlib import Path
import itertools
from models import FileNode, FolderNode
from project_manager import ProjectManager
from config import config
import logic
import database
from strategies import utils, find_duplicates_strategy
from threading_utils import TaskRunner
import threading

logger = logging.getLogger(__name__)

class AppController:
    def __init__(self, view):
        self.view = view
        self.project_manager = ProjectManager(self)
        self.task_runner = TaskRunner(self.view)

        # --- UI variables ---
        self.move_to_path = tk.StringVar()
        self.file_type_filter = tk.StringVar(value="all")

        # --- Comparison options ---
        self.include_subfolders = tk.BooleanVar()
        self.compare_name = tk.BooleanVar(value=False)
        self.compare_date = tk.BooleanVar(value=False)
        self.compare_size = tk.BooleanVar(value=True)
        self.compare_content_md5 = tk.BooleanVar(value=False)
        self.compare_histogram = tk.BooleanVar(value=False)
        self.histogram_method = tk.StringVar(value='Correlation')
        self.histogram_threshold = tk.StringVar(value='0.9')
        self.compare_llm = tk.BooleanVar(value=False)
        self.llm_similarity_threshold = tk.StringVar(value='0.8')
        

        # --- Folder Structures ---
        self.folder_structures = {}

        # --- LLM Engine ---
        self.llm_engine = None
        self.llm_engine_loading = False

        self._bind_variables_to_view()
        self.view.setup_ui()

    def build_active_folders(self, event=None):
        """Builds metadata for all folders in the list."""
        logger.info("Build triggered.")
        folders_to_build = self.view.folder_list_box.get(0, tk.END)
        if not folders_to_build:
            messagebox.showwarning("Build Warning", "No folders to build. Please add folders to the list.")
            return

        self.view.action_button.config(state='disabled')
        for btn in self.view.build_buttons: btn.config(state='disabled')

        remaining_tasks = len(folders_to_build)
        lock = threading.Lock()

        def on_task_finally():
            nonlocal remaining_tasks
            with lock:
                remaining_tasks -= 1
                if remaining_tasks == 0:
                    logger.info("All build tasks completed.")
                    self.view.update_status("All builds finished.")
                    for btn in self.view.build_buttons: btn.config(state='normal')
                    self.view.action_button.config(state='normal')

        for i, folder_path in enumerate(folders_to_build, 1):
            self._build_metadata(folder_path, i, on_task_finally)

    def _bind_variables_to_view(self):
        # This makes the controller's variables directly usable by the view's widgets
        self.view.move_to_path = self.move_to_path
        self.view.file_type_filter = self.file_type_filter
        self.view.include_subfolders = self.include_subfolders
        self.view.compare_name = self.compare_name
        self.view.compare_date = self.compare_date
        self.view.compare_size = self.compare_size
        self.view.compare_content_md5 = self.compare_content_md5
        self.view.compare_histogram = self.compare_histogram
        self.view.histogram_method = self.histogram_method
        self.view.histogram_threshold = self.histogram_threshold
        self.view.compare_llm = self.compare_llm
        self.view.llm_similarity_threshold = self.llm_similarity_threshold
        

        # Pass the controller instance to the view
        self.view.controller = self

    def clear_all_settings(self):
        self.move_to_path.set("")
        self.include_subfolders.set(False)
        self.compare_name.set(True)
        self.compare_date.set(False)
        self.compare_size.set(False)
        self.compare_content_md5.set(False)
        self.compare_histogram.set(False)
        self.compare_llm.set(False)
        self.llm_similarity_threshold.set('0.8')
        self.histogram_method.set('Correlation')
        self.histogram_threshold.set('0.9')
        self.folder_structures = {}
        if hasattr(self.view, 'results_tree'):
            for i in self.view.results_tree.get_children():
                self.view.results_tree.delete(i)
        if hasattr(self.view, 'folder_list_box') and self.view.folder_list_box:
            self.view.folder_list_box.delete(0, tk.END)

    def _dict_to_structure(self, node_list):
        structure = []
        for node_dict in node_list:
            if node_dict['type'] == 'folder':
                node = FolderNode(Path(node_dict['fullpath']))
                node.content = self._dict_to_structure(node_dict.get('content', []))
                structure.append(node)
            elif node_dict['type'] == 'file':
                node = FileNode(Path(node_dict['fullpath']), node_dict.get('metadata'))
                structure.append(node)
        return structure

    def _ensure_llm_engine_loaded(self):
        """
        Checks if the LLM engine is loaded, and if not, starts the loading
        process in a background thread.
        Returns True if the engine is ready, False otherwise.
        """
        if self.llm_engine:
            return True
        if self.llm_engine_loading:
            messagebox.showinfo("LLM Engine Loading", "The LLM engine is currently loading. Please try again in a moment.")
            return False
        if not config.get("use_llm", True):
            return False

        self.llm_engine_loading = True
        self.view.llm_checkbox.config(state='disabled')
        self.view.action_button.config(state='disabled')
        self.view.update_status("Starting to load LLM engine...")

        thread = threading.Thread(target=self._load_llm_engine_task)
        thread.daemon = True
        thread.start()

        return False

    def _load_llm_engine_task(self):
        """The actual task of loading the LLM engine. To be run in a thread."""
        try:
            from ai_engine.engine import LlavaEmbeddingEngine
            self.view.update_status("Initializing LLM engine...")
            logger.info("Initializing LLM engine...")
            # In the future, we can pass gpu_layers from a config
            self.llm_engine = LlavaEmbeddingEngine()
            self.view.update_status("LLM engine loaded successfully.")
            logger.info("LLM engine loaded successfully.")
        except Exception as e:
            self.llm_engine = None
            if hasattr(self.view, 'llm_checkbox'):
                self.view.llm_checkbox.config(state='disabled')
            self.view.update_status("LLM engine failed to load. LLM features disabled.")
            logger.error("LLM engine failed to load.", exc_info=True)
            messagebox.showwarning("LLM Engine Error",
                                   f"""Could not initialize the LLaVA model. Please ensure model files exist in the /models directory.\n\nError: {e}"""
                                   )
        finally:
            # Re-enable UI elements and reset loading flag
            self.llm_engine_loading = False
            self.view.action_button.config(state='normal')
            if config.get("use_llm", True):
                 if hasattr(self.view, 'llm_checkbox'):
                    self.view.llm_checkbox.config(state='normal')

    def build_folders(self):
        """Builds metadata for all folders in the list."""
        folders_to_build = self.view.folder_list_box.get(0, tk.END)
        if not folders_to_build:
            messagebox.showwarning("Build Warning", "No folders to build. Please add folders to the list.")
            return

        self.view.action_button.config(state='disabled')
        for btn in self.view.build_buttons: btn.config(state='disabled')

        remaining_tasks = len(folders_to_build)
        lock = threading.Lock()

        def on_task_finally():
            nonlocal remaining_tasks
            with lock:
                remaining_tasks -= 1
                if remaining_tasks == 0:
                    logger.info("All build tasks completed.")
                    self.view.update_status("All builds finished.")
                    for btn in self.view.build_buttons: btn.config(state='normal')
                    self.view.action_button.config(state='normal')

        for i, folder_path in enumerate(folders_to_build, 1):
            self._build_metadata(folder_path, i, on_task_finally)

    def _build_metadata(self, folder_path, folder_index, on_finally_callback=None):
        # With JSON support removed, we only call the DB version.
        self._build_metadata_db(folder_path, folder_index, on_finally_callback)

    def _build_metadata_db(self, path, folder_index, on_finally_callback=None):
        logger.info(f"Queueing metadata build for folder {folder_index} at path: {path} (DB)")

        if not self.project_manager.save_project():
            logger.warning("Metadata build aborted: project save was cancelled.")
            if on_finally_callback: on_finally_callback()
            return

        if not path or not Path(path).is_dir():
            logger.error(f"Invalid directory for folder {folder_index}: {path}")
            messagebox.showerror("Error", f"Please select a valid directory for Folder {folder_index}.")
            if on_finally_callback: on_finally_callback()
            return

        self.view.update_status(f"Building metadata for Folder {folder_index}...")

        def build_task():
            conn = database.get_db_connection(self.project_manager.current_project_path)
            inaccessible_paths = logic.build_folder_structure_db(
                conn, folder_index, path, self.include_subfolders.get()
            )
            conn.close()
            return inaccessible_paths

        def on_success(inaccessible_paths):
            logger.info(f"Successfully built folder structure for folder {folder_index} into DB.")
            self.view.update_status(f"Metadata built for Folder {folder_index}. Saving project...")
            self.project_manager.save_project()
            success_message = f"Metadata built and saved for Folder {folder_index}."
            if inaccessible_paths:
                warning_message = (f"{success_message}\n\nWarning: The following files or folders could not be accessed and were skipped:\n\n" + "\n".join(f"- {p}" for p in inaccessible_paths[:10]))
                if len(inaccessible_paths) > 10: warning_message += f"...and {len(inaccessible_paths) - 10} more."
                messagebox.showwarning("Build Warning", warning_message)
            else:
                messagebox.showinfo("Success", success_message)
            logger.info(f"Metadata build and save successful for folder {folder_index}.")

        def on_error(e):
            logger.error(f"Failed to build metadata for folder {folder_index} into DB.", exc_info=e)
            messagebox.showerror("Build Error", f"An error occurred during metadata build:\n{e}")

        final_callback = on_finally_callback if on_finally_callback else lambda: None
        self.task_runner.run_task(build_task, on_success, on_error, final_callback)

    def run_action(self, event=None):
        opts = self.project_manager._gather_settings()

        if opts.get('compare_llm') and not self._ensure_llm_engine_loaded():
            return

        folders_in_list = self.view.folder_list_box.get(0, tk.END)
        num_folders = len(folders_in_list)

        if num_folders == 0:
            messagebox.showerror("Error", "Please add at least one folder to analyze.")
            return

        self.view.action_button.config(state='disabled')
        for btn in self.view.build_buttons: btn.config(state='disabled')
        for i in self.view.results_tree.get_children(): self.view.results_tree.delete(i)
        self.view.progress_bar['value'] = 0
        logger.info(f"Queueing action with options: {opts}")

        def action_task():
            logger.info("Background task starting: metadata calculation and strategy execution.")
            return self._run_action_db(opts, folders_in_list)

        def on_success(all_results):
            logger.info(f"Action finished successfully.")
            try:
                total_matches = 0
                if not all_results:
                    message = "No duplicate files found."
                    self.view.results_tree.insert('', tk.END, values=(message, "", ""), tags=('info_row',))
                else:
                    total_matches = sum(len(group) for group in all_results)
                    for i, group in enumerate(all_results, 1):
                        header_text = f"Duplicate Set {i} ({len(group)} files)"
                        parent = self.view.results_tree.insert('', tk.END, values=(header_text, "", "", ""), open=True, tags=('header_row',))
                        for file_info in group:
                            size = file_info.get('size', 'N/A')
                            path_dir = file_info.get('path', '')
                            file_name = file_info.get('name', '') # Get the actual file name
                            folder_index = file_info.get('folder_index')
                            base_path = folders_in_list[folder_index - 1]
                            display_path = str(Path(path_dir) / file_name) if path_dir else file_name
                            full_path = str(Path(base_path) / display_path)
                            self.view.results_tree.insert(parent, tk.END, values=(f"  {file_name}", size, full_path, display_path), tags=('file_row',))
                
                if total_matches == 0 and all_results:
                    message = "No matching files found."
                    self.view.results_tree.insert('', tk.END, values=(message, "", ""), tags=('info_row',))

                messagebox.showinfo("Success", f"Operation completed successfully. Found {total_matches} total matches.")
            except Exception as e:
                logger.error("Error displaying results:", exc_info=True)
                messagebox.showerror("Error", f"An error occurred while displaying the results:\n{e}")

        def on_error(e):
            logger.critical("An unexpected error occurred during the main action.", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

        def on_finally():
            self.view.update_status("Ready.")
            self.view.progress_bar['value'] = 0
            self.view.action_button.config(state='normal')
            for btn in self.view.build_buttons: btn.config(state='normal')
            logger.info("Action finished.")

        self.task_runner.run_task(action_task, on_success, on_error, on_finally)

    def _run_action_db(self, opts, folders_in_list):
        logger.info(f"Running DB action.")
        conn = database.get_db_connection(self.project_manager.current_project_path)
        file_filter = self.file_type_filter.get()

        for path in folders_in_list:
            folder_index = folders_in_list.index(path) + 1
            self.task_runner.post_to_main_thread(self.view.update_status, f"Calculating metadata for {Path(path).name}...")
            utils.calculate_metadata_db(conn, folder_index, path, opts, file_type_filter=file_filter, llm_engine=self.llm_engine)

        self.task_runner.post_to_main_thread(self.view.update_status, "Finding duplicates...")
        all_results = find_duplicates_strategy.run(conn, opts)

        conn.close()
        return all_results
