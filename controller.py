import tkinter as tk
import logging
from project_manager import ProjectManager
from config import config

logger = logging.getLogger(__name__)

class AppController:
    def __init__(self, view):
        self.view = view
        self.project_manager = ProjectManager(self)

        # --- UI variables ---
        self.folder1_path = tk.StringVar()
        self.folder2_path = tk.StringVar()
        self.app_mode = tk.StringVar(value="compare")
        self.search_query = tk.StringVar()
        self.move_to_path = tk.StringVar()
        self.file_type_filter = tk.StringVar(value="all")

        # --- Comparison options ---
        self.include_subfolders = tk.BooleanVar()
        self.compare_name = tk.BooleanVar(value=True)
        self.compare_date = tk.BooleanVar()
        self.compare_size = tk.BooleanVar()
        self.compare_content_md5 = tk.BooleanVar()
        self.compare_histogram = tk.BooleanVar()
        self.histogram_method = tk.StringVar(value='Correlation')
        self.histogram_threshold = tk.StringVar(value='0.9')
        self.compare_llm = tk.BooleanVar()

        # --- Folder Structures ---
        self.folder1_structure = None
        self.folder2_structure = None

        # --- LLM Engine ---
        self.llm_engine = None
        self.llm_engine_loading = False

        self._bind_variables_to_view()
        self.view.setup_ui()

    def _bind_variables_to_view(self):
        # This makes the controller's variables directly usable by the view's widgets
        self.view.folder1_path = self.folder1_path
        self.view.folder2_path = self.folder2_path
        self.view.app_mode = self.app_mode
        self.view.search_query = self.search_query
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

        # Pass the controller instance to the view
        self.view.controller = self

    def clear_all_settings(self):
        self.folder1_path.set("")
        self.folder2_path.set("")
        self.move_to_path.set("")
        self.include_subfolders.set(False)
        self.compare_name.set(True)
        self.compare_date.set(False)
        self.compare_size.set(False)
        self.compare_content_md5.set(False)
        self.compare_histogram.set(False)
        self.compare_llm.set(False)
        self.histogram_method.set('Correlation')
        self.histogram_threshold.set('0.9')
        self.folder1_structure = None
        self.folder2_structure = None
        if hasattr(self.view, 'results_tree'):
            for i in self.view.results_tree.get_children():
                self.view.results_tree.delete(i)

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
                                   f"Could not initialize the LLaVA model. Please ensure model files exist in the /models directory.\n\nError: {e}")
        finally:
            # Re-enable UI elements and reset loading flag
            self.llm_engine_loading = False
            self.view.action_button.config(state='normal')
            if config.get("use_llm", True):
                 if hasattr(self.view, 'llm_checkbox'):
                    self.view.llm_checkbox.config(state='normal')

    def _build_metadata(self, folder_num):
        path_var = self.folder1_path if folder_num == 1 else self.folder2_path
        path = path_var.get()
        logger.info(f"Starting metadata build for folder {folder_num} at path: {path}")

        try:
            for btn in self.view.build_buttons: btn.config(state='disabled')
            self.view.update_status(f"Building metadata for Folder {folder_num}...")

            if not self.project_manager.save_project():
                logger.warning("Metadata build aborted because project save was cancelled.")
                messagebox.showwarning("Save Cancelled", "Metadata build aborted because the project was not saved.")
                return

            if not path or not Path(path).is_dir():
                logger.error(f"Invalid directory for folder {folder_num}: {path}")
                messagebox.showerror("Error", f"Please select a valid directory for Folder {folder_num}.")
                return

            structure = logic.build_folder_structure(path)
            if folder_num == 1: self.folder1_structure = structure
            else: self.folder2_structure = structure
            logger.info(f"Successfully built folder structure for folder {folder_num}.")

            self.view.update_status(f"Metadata built for Folder {folder_num}. Saving project...")
            self.project_manager.save_project()
            messagebox.showinfo("Success", f"Metadata built and saved for Folder {folder_num}.")
            logger.info(f"Metadata build and save successful for folder {folder_num}.")

        except Exception as e:
            logger.error(f"Failed to build metadata for folder {folder_num}.", exc_info=True)
            messagebox.showerror("Build Error", f"An error occurred during metadata build:\n{e}")
        finally:
            self.view.update_status("Ready.")
            for btn in self.view.build_buttons: btn.config(state='normal')

    def run_action(self):
        opts = self.project_manager._gather_settings()['options']
        if opts.get('compare_llm'):
            if not self._ensure_llm_engine_loaded():
                return # Engine is not ready, so we abort the action

        for i in self.view.results_tree.get_children():
            self.view.results_tree.delete(i)
        mode = self.app_mode.get()
        logger.info(f"Running action '{mode}' with options: {opts}")

        try:
            # --- Progress Bar Setup ---
            self.view.progress_bar['value'] = 0

            total_llm_files = 0

            def progress_callback(message, processed_count):
                progress_percentage = (processed_count / total_llm_files) * 100 if total_llm_files > 0 else 0
                self.view.update_status(message, progress_percentage)

            # --- Metadata Generation and Persistence ---
            self.view.update_status("Calculating metadata...")
            logger.info("Calculating metadata...")

            info1, info2 = None, None
            file_filter = self.file_type_filter.get()
            if self.folder1_structure:
                base_path1 = self.folder1_path.get()
                info1, total1 = utils.flatten_structure(self.folder1_structure, base_path1, opts, file_type_filter=file_filter, llm_engine=self.llm_engine, progress_callback=progress_callback)
                total_llm_files += total1
                self.view.progress_bar['maximum'] = total_llm_files if total_llm_files > 0 else 100
                self.view._update_filenode_metadata(self.folder1_structure, info1, base_path1)
                logger.info(f"Flattened structure for folder 1. Found {len(info1)} items.")

            if self.folder2_structure:
                base_path2 = self.folder2_path.get()
                info2, total2 = utils.flatten_structure(self.folder2_structure, base_path2, opts, file_type_filter=file_filter, llm_engine=self.llm_engine, progress_callback=progress_callback)
                total_llm_files += total2
                self.view.progress_bar['maximum'] = total_llm_files if total_llm_files > 0 else 100
                self.view._update_filenode_metadata(self.folder2_structure, info2, base_path2)
                logger.info(f"Flattened structure for folder 2. Found {len(info2)} items.")

            if self.project_manager.save_project():
                self.view.update_status("Metadata calculated and project saved.")
                logger.info("Metadata calculated and project saved.")
            else:
                self.view.update_status("Metadata calculated, but project save failed.")
                logger.warning("Metadata calculated, but project save failed.")
                messagebox.showwarning("Save Failed", "Could not save the project with new metadata.")

            # --- Strategy Execution ---
            logger.info(f"Executing '{mode}' strategy.")
            if mode == "compare":
                if not info1 or not info2:
                    logger.error("Compare action failed: metadata for both folders is required.")
                    messagebox.showerror("Error", "Please build metadata for both folders before comparing.")
                    return

                results = find_common_strategy.run(info1, info2, opts)
                logger.info(f"Compare action finished. Found {len(results)} matching files.")
                if not results:
                    self.view.results_tree.insert('', tk.END, values=("No matching files found.", "", ""), tags=('info_row',))
                else:
                    for file_info in results:
                        size = file_info.get('compare_size', 'N/A')
                        relative_path = file_info.get('relative_path', '')
                        file_name = Path(relative_path).name
                        self.view.results_tree.insert('', tk.END, values=(file_name, size, relative_path), tags=('file_row',))

            elif mode == "duplicates":
                if not info1:
                    logger.error("Duplicates action failed: metadata for the folder is required.")
                    messagebox.showerror("Error", "Please build metadata for the folder before finding duplicates.")
                    return

                results = find_duplicates_strategy.run(info1, opts)
                logger.info(f"Duplicates action finished. Found {len(results)} duplicate groups.")
                if not results:
                    self.view.results_tree.insert('', tk.END, values=("No duplicate files found.", "", ""), tags=('info_row',))
                else:
                    for i, group in enumerate(results, 1):
                        # Add a header row for the duplicate set
                        header_text = f"Duplicate Set {i} ({len(group)} files)"
                        parent = self.view.results_tree.insert('', tk.END, values=(header_text, "", ""), open=True, tags=('header_row',))
                        for file_info in group:
                            size = file_info.get('compare_size', 'N/A')
                            relative_path = file_info.get('relative_path', '')
                            file_name = Path(relative_path).name
                            self.view.results_tree.insert(parent, tk.END, values=(f"  {file_name}", size, relative_path), tags=('file_row',))

            elif mode == "search":
                if not info1:
                    logger.error("Search action failed: metadata for the folder is required.")
                    messagebox.showerror("Error", "Please build metadata for the folder before searching.")
                    return

                results = info1.values()
                logger.info(f"Search action finished. Found {len(results)} matching files.")
                if not results:
                    self.view.results_tree.insert('', tk.END, values=(f"No files found matching the filter.", "", ""), tags=('info_row',))
                else:
                    for file_info in results:
                        size = file_info.get('compare_size', 'N/A')
                        relative_path = file_info.get('relative_path', '')
                        file_name = Path(relative_path).name
                        self.view.results_tree.insert('', tk.END, values=(file_name, size, relative_path), tags=('file_row',))
        except Exception as e:
            logger.critical("An unexpected error occurred during the main action.", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred during comparison:\n{e}")
        finally:
            self.view.update_status("Ready.")
            self.view.progress_bar['value'] = 0
            logger.info("Action finished.")
