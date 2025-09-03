import json
import logging
from pathlib import Path
from tkinter import filedialog, messagebox
from models import FileNode, FolderNode

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
        metadata = {}
        if self.controller.folder1_structure:
            metadata["folder1"] = [node.to_dict() for node in self.controller.folder1_structure]
        if self.controller.folder2_structure:
            metadata["folder2"] = [node.to_dict() for node in self.controller.folder2_structure]
        if metadata:
            settings["metadata"] = metadata
        return settings

    def save_project(self):
        if not self.current_project_path:
            return self.save_project_as()
        logger.info(f"Saving project to {self.current_project_path}")
        try:
            with open(self.current_project_path, 'w') as f:
                json.dump(self._gather_settings(), f, indent=4)
            logger.info("Project saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to save project to {self.current_project_path}", exc_info=True)
            messagebox.showerror("Error", f"Could not save project file:\n{e}")
            return False

    def save_project_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".cfp", filetypes=[("Comparison Project Files", "*.cfp")])
        if not path:
            logger.info("'Save As' operation cancelled by user.")
            return False
        self.current_project_path = path
        self.controller.view.root.title(f"{Path(path).name} - Folder Comparison Tool")
        logger.info(f"Project path set to {path}. Proceeding to save.")
        return self.save_project()

    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("Comparison Project Files", "*.cfp")])
        if not path:
            logger.info("'Load Project' operation cancelled by user.")
            return
        logger.info(f"Loading project from: {path}")
        try:
            with open(path, 'r') as f:
                settings = json.load(f)

            self.controller.clear_all_settings()

            self.controller.app_mode.set(settings.get("app_mode", "compare"))
            self.controller.file_type_filter.set(settings.get("file_type_filter", "all"))
            self.controller.folder1_path.set(settings.get("folder1_path", ""))
            self.controller.folder2_path.set(settings.get("folder2_path", ""))
            self.controller.move_to_path.set(settings.get("move_to_path", ""))

            opts = settings.get("options", {})
            for opt, val in opts.items():
                if hasattr(self.controller, opt) and hasattr(getattr(self.controller, opt), 'set'):
                    getattr(self.controller, opt).set(val)

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

    def new_project(self):
        logger.info("Creating new project.")
        self.controller.clear_all_settings()
        self.current_project_path = None
        self.controller.view.root.title("New Project - Folder Comparison Tool")
        self.controller.view._set_main_ui_state('normal')
