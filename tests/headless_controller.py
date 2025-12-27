import os
import sys
import tkinter as tk
from controller import AppController
from unittest.mock import MagicMock

class SynchronousTaskRunner:
    def __init__(self, view):
        self.view = view

    def run_task(self, task_func, on_success=None, on_error=None, on_finally=None):
        try:
            result = task_func()
            if on_success:
                on_success(result)
        except Exception as e:
            # logger.error("An error occurred in the synchronous task", exc_info=True)
            if on_error:
                on_error(e)
        finally:
            if on_finally:
                on_finally()
                
class HeadlessAppController(AppController):
    """A version of AppController that doesn't require a real UI."""
    def __init__(self, view=None):
        if view is None:
            view = MagicMock()
        
        # Initialize mock variables instead of real tk variables
        # to avoid "no default root window" errors
        self.view = view
        self.is_test = True
        
        self.move_to_path = MagicMock()
        self.move_to_path.get.return_value = ""
        self.file_type_filter = MagicMock()
        self.file_type_filter.get.return_value = "all"
        
        self.include_subfolders = MagicMock()
        self.include_subfolders.get.return_value = False
        self.compare_name = MagicMock()
        self.compare_name.get.return_value = False
        self.compare_date = MagicMock()
        self.compare_date.get.return_value = False
        self.compare_size = MagicMock()
        self.compare_size.get.return_value = True
        self.compare_content_md5 = MagicMock()
        self.compare_content_md5.get.return_value = False
        self.compare_histogram = MagicMock()
        self.compare_histogram.get.return_value = False
        self.histogram_method = MagicMock()
        self.histogram_method.get.return_value = "Correlation"
        self.histogram_threshold = MagicMock()
        self.histogram_threshold.get.return_value = "0.9"
        self.compare_llm = MagicMock()
        self.compare_llm.get.return_value = False
        self.llm_similarity_threshold = MagicMock()
        self.llm_similarity_threshold.get.return_value = "0.8"
        
        try:
            from threading_utils import TaskRunner
            from project_manager import ProjectManager
        except ImportError:
            # Fallback for different test runner environments
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
            from threading_utils import TaskRunner
            from project_manager import ProjectManager
        
        self.project_manager = ProjectManager(self)
        self.task_runner = SynchronousTaskRunner(self.view)
        self.repository = None
        self.folder_structures = {}
        self.llm_engine = None
        self.llm_engine_loading = False

        self._bind_variables_to_view()
        # We don't call view.setup_ui() here as we might want to mock things first
    
    def build_folders(self):
        """Mock build_folders for user bug test."""
        # The real controller uses run_action()
        self.run_action()

    def close(self):
        """Close resources."""
        if self.repository:
            self.repository.close()
        self.repository = None
