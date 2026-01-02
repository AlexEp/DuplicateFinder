import json
import logging
from pathlib import Path
from tkinter import filedialog, messagebox
from models import FileNode, FolderNode
import database

from domain.comparison_options import ComparisonOptions

logger = logging.getLogger(__name__)

from repositories.sqlite_repository import SQLiteRepository

logger = logging.getLogger(__name__)

class ProjectManager:
    def __init__(self, app_controller):
        self.controller = app_controller
        self._current_project_path = None

    @property
    def current_project_path(self):
        return self._current_project_path

    @current_project_path.setter
    def current_project_path(self, value):
        self._current_project_path = value
        if value:
            self._init_repository(value)

    def _init_repository(self, path: str):
        if self.controller.repository:
            self.controller.repository.close()
        self.controller.repository = SQLiteRepository(path)
        self.controller.project_service.set_repository(self.controller.repository)
        self.controller.comparison_service._repository = self.controller.repository
        logger.info(f"Initialized repository for: {path}")

    def get_options(self) -> ComparisonOptions:
        """Returns a ComparisonOptions value object populated from the current UI state."""
        strategy_opts = {}
        
        # Get all registered strategies
        from strategies.strategy_registry import get_all_strategies
        strategies = get_all_strategies()
        for strategy in strategies:
            meta = strategy.metadata
            key = meta.option_key
            if hasattr(self.controller, key):
                strategy_opts[key] = getattr(self.controller, key).get()
            
            if meta.has_threshold:
                threshold_key = f"{key}_threshold"
                if key == 'compare_histogram': threshold_key = 'histogram_threshold'
                elif key == 'compare_llm': threshold_key = 'llm_similarity_threshold'
                
                if hasattr(self.controller, threshold_key):
                    val = getattr(self.controller, threshold_key).get()
                    try:
                        strategy_opts[threshold_key] = float(val)
                    except (ValueError, TypeError):
                        strategy_opts[threshold_key] = meta.default_threshold or 0.8
        
        # Add non-strategy options
        # We also need to add 'histogram_method' if it's still hardcoded or handled elsewhere
        if hasattr(self.controller, 'histogram_method'):
            strategy_opts['histogram_method'] = self.controller.histogram_method.get()

        return ComparisonOptions(
            file_type_filter=self.controller.file_type_filter.get(),
            include_subfolders=self.controller.include_subfolders.get(),
            move_to_path=self.controller.move_to_path.get(),
            options=strategy_opts
        )

    def _gather_settings(self):
        """Maintains legacy dictionary format for database persistence."""
        return self.get_options().to_save_dict()

    def save_project(self):
        if not self.current_project_path:
            return self.save_project_as()
        
        # All projects are now DB based
        return self._save_project_db()

    def _save_project_db(self):
        logger.info(f"Saving project to {self.current_project_path} (DB)")
        try:
            conn = database.get_db_connection(self.current_project_path)
            settings = self._gather_settings()
            database.save_setting(conn, 'project_settings', settings)
            conn.close()
            logger.info("Project saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to save project to {self.current_project_path}", exc_info=True)
            messagebox.showerror("Error", f"Could not save project file:\n{e}")
            return False

    def save_project_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".cfp-db",
            filetypes=[("Comparison Project DB", "*.cfp-db")]
        )
        if not path:
            logger.info("'Save As' operation cancelled by user.")
            return False
        self.current_project_path = path
        self.controller.view.root.title(f"{Path(path).name} - Folder Comparison Tool")
        logger.info(f"Project path set to {path}. Proceeding to save.")
        
        if self.current_project_path.endswith(".cfp-db"):
            # Create DB and tables if it's a new DB project
            conn = database.get_db_connection(self.current_project_path)
            database.create_tables(conn)
            conn.close()

        return self.save_project()

    def load_project(self):
        path = filedialog.askopenfilename(
            filetypes=[("Comparison Project Files", "*.cfp-db *.cfp"), ("All files", "*.* ")]
        )
        if not path:
            logger.info("'Load Project' operation cancelled by user.")
            return

        if not path.endswith(".cfp-db"):
            messagebox.showerror("Error", "Invalid project file format. Only .cfp-db files are supported.")
            return
        self._load_project_db(path)

    def _load_project_db(self, path):
        logger.info(f"Loading project from: {path} (DB)")
        try:
            conn = database.get_db_connection(path)
            database.create_tables(conn)
            settings = database.load_setting(conn, 'project_settings')
            sources = database.get_sources(conn)
            conn.close()

            self.controller.clear_all_settings()
            if settings:
                self._apply_settings(settings)

            # In DB mode, folder structures are not loaded into memory upfront.
            # They are queried when needed.
            self.controller.folder_structures = {}

            self.controller.view.folder_list_box.config(state='normal')
            self.controller.view.folder_list_box.delete(0, 'end')
            for _, folder_path in sources:
                self.controller.view.folder_list_box.insert('end', folder_path)
            self.controller.view.folder_list_box.config(state='disabled')
            self.controller.view.update_action_button_text()


            self.current_project_path = path
            self.controller.view.root.title(f"{Path(path).name} - Folder Comparison Tool")
            self.controller.view._set_main_ui_state('normal')
            logger.info(f"Successfully loaded project: {path}")
        except Exception as e:
            logger.error(f"Failed to load project file: {path}", exc_info=True)
            messagebox.showerror("Error", f"Could not load project file:\n{e}")

    def _apply_settings(self, settings):
        self.controller.file_type_filter.set(settings.get("file_type_filter", "all"))
        self.controller.move_to_path.set(settings.get("move_to_path", ""))

        opts = settings.get("options", {})
        for opt, val in opts.items():
            if hasattr(self.controller, opt) and hasattr(getattr(self.controller, opt), 'set'):
                getattr(self.controller, opt).set(val)

        # The folder list is now loaded from the sources table, so this is no longer needed.
        # if "compare_folder_list" in settings and self.controller.view.folder_list_box:
        #     self.controller.view.folder_list_box.delete(0, "end")
        #     for folder in settings["compare_folder_list"]:
        #         self.controller.view.folder_list_box.insert("end", folder)

    def create_new_project_file(self, path, folders):
        logger.info(f"Creating new project file at: {path}")
        self.current_project_path = path
        conn = database.get_db_connection(self.current_project_path)
        try:
            database.create_tables(conn)
            database.clear_sources(conn) # Clear existing sources for a new project
            for folder in folders:
                database.add_source(conn, folder)

            settings = self._gather_settings()
            database.save_setting(conn, 'project_settings', settings)

            self.controller.view.root.title(f"{Path(path).name} - Folder Comparison Tool")
            logger.info(f"Successfully created and saved new project: {path}")
        except Exception as e:
            logger.error(f"Failed to create new project file: {path}", exc_info=True)
            messagebox.showerror("Error", f"Could not create project file:\n{e}")
            self.current_project_path = None
        finally:
            conn.close()

    def add_folder(self, folder_path):
        """Add a folder to the current project."""
        logger.info(f"Adding folder to project: {folder_path}")
        if not self.current_project_path:
            if self.controller.view.folder_list_box:
                self.controller.view.folder_list_box.insert('end', folder_path)
            return

        conn = database.get_db_connection(self.current_project_path)
        try:
            database.add_source(conn, folder_path)
            # Update view
            if self.controller.view.folder_list_box:
                self.controller.view.folder_list_box.config(state='normal')
                self.controller.view.folder_list_box.insert('end', folder_path)
                self.controller.view.folder_list_box.config(state='disabled')
            self.controller.view.update_action_button_text()
        finally:
            conn.close()

    def new_project(self):
        # This method is now primarily a pass-through.
        # The main logic is handled by the UI in `show_new_project_dialog`.
        logger.info("New project creation initiated by user.")
        self.controller.view.show_new_project_dialog()
