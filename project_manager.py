import json
import logging
from pathlib import Path
from tkinter import filedialog, messagebox
from models import FileNode, FolderNode
import database

logger = logging.getLogger(__name__)

class ProjectManager:
    def __init__(self, app_controller):
        self.controller = app_controller
        self.current_project_path = None

    def _gather_settings(self):
        settings = {
            "app_mode": self.controller.app_mode.get(),
            "file_type_filter": self.controller.file_type_filter.get(),
            "folder1_path": self.controller.folder1_path.get(),
            "folder2_path": self.controller.folder2_path.get(),
            "move_to_path": self.controller.move_to_path.get(),
            "options": {
                "include_subfolders": self.controller.include_subfolders.get(),
                "compare_name": self.controller.compare_name.get(),
                "compare_date": self.controller.compare_date.get(),
                "compare_size": self.controller.compare_size.get(),
                "compare_content_md5": self.controller.compare_content_md5.get(),
                "compare_histogram": self.controller.compare_histogram.get(),
                "compare_llm": self.controller.compare_llm.get(),
                "histogram_method": self.controller.histogram_method.get(),
                "histogram_threshold": self.controller.histogram_threshold.get(),
                "llm_similarity_threshold": self.controller.llm_similarity_threshold.get()
            }
        }
        # Metadata is handled by the database now
        return settings

    def save_project(self):
        if not self.current_project_path:
            return self.save_project_as()
        
        if self.current_project_path.endswith(".cfp-db"):
            return self._save_project_db()
        else:
            return self._save_project_json()

    def _save_project_json(self):
        logger.info(f"Saving project to {self.current_project_path} (JSON)")
        try:
            settings = self._gather_settings()
            metadata = {}
            if self.controller.folder1_structure:
                metadata["folder1"] = [node.to_dict() for node in self.controller.folder1_structure]
            if self.controller.folder2_structure:
                metadata["folder2"] = [node.to_dict() for node in self.controller.folder2_structure]
            if metadata:
                settings["metadata"] = metadata

            with open(self.current_project_path, 'w') as f:
                json.dump(settings, f, indent=4)
            logger.info("Project saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to save project to {self.current_project_path}", exc_info=True)
            messagebox.showerror("Error", f"Could not save project file:\n{e}")
            return False

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
            filetypes=[("Comparison Project DB", "*.cfp-db"), ("Comparison Project JSON", "*.cfp")]
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

        if path.endswith(".cfp-db"):
            self._load_project_db(path)
        else:
            self._load_project_json(path)

    def _load_project_json(self, path):
        logger.info(f"Loading project from: {path} (JSON)")
        try:
            with open(path, 'r') as f:
                settings = json.load(f)

            self.controller.clear_all_settings()
            self._apply_settings(settings)

            if "metadata" in settings:
                if "folder1" in settings["metadata"]:
                    self.controller.folder1_structure = self.controller._dict_to_structure(settings["metadata"]["folder1"])
                if "folder2" in settings["metadata"]:
                    self.controller.folder2_structure = self.controller._dict_to_structure(settings["metadata"]["folder2"])

            self.current_project_path = path
            self.controller.view.root.title(f"{Path(path).name} - Folder Comparison Tool")
            self.controller.view._set_main_ui_state('normal')
            logger.info(f"Successfully loaded project: {path}")
        except Exception as e:
            logger.error(f"Failed to load project file: {path}", exc_info=True)
            messagebox.showerror("Error", f"Could not load project file:\n{e}")

    def _load_project_db(self, path):
        logger.info(f"Loading project from: {path} (DB)")
        try:
            conn = database.get_db_connection(path)
            settings = database.load_setting(conn, 'project_settings')
            conn.close()

            self.controller.clear_all_settings()
            if settings:
                self._apply_settings(settings)

            # In DB mode, folder structures are not loaded into memory upfront.
            # They are queried when needed.
            self.controller.folder1_structure = None
            self.controller.folder2_structure = None

            self.current_project_path = path
            self.controller.view.root.title(f"{Path(path).name} - Folder Comparison Tool")
            self.controller.view._set_main_ui_state('normal')
            logger.info(f"Successfully loaded project: {path}")
        except Exception as e:
            logger.error(f"Failed to load project file: {path}", exc_info=True)
            messagebox.showerror("Error", f"Could not load project file:\n{e}")

    def _apply_settings(self, settings):
        self.controller.app_mode.set(settings.get("app_mode", "compare"))
        self.controller.file_type_filter.set(settings.get("file_type_filter", "all"))
        self.controller.folder1_path.set(settings.get("folder1_path", ""))
        self.controller.folder2_path.set(settings.get("folder2_path", ""))
        self.controller.move_to_path.set(settings.get("move_to_path", ""))

        opts = settings.get("options", {})
        for opt, val in opts.items():
            if hasattr(self.controller, opt) and hasattr(getattr(self.controller, opt), 'set'):
                getattr(self.controller, opt).set(val)

    def new_project(self):
        logger.info("Creating new project.")
        self.controller.clear_all_settings()
        self.current_project_path = None
        self.controller.view.root.title("New Project - Folder Comparison Tool")
        self.controller.view._set_main_ui_state('normal')