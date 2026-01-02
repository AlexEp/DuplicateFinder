import tkinter as tk
import logging
from ui import FolderComparisonApp
from controller import AppController
from logger_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    try:
        root = tk.Tk()
        
        from services.file_service import FileService
        from services.comparison_service import ComparisonService
        from services.project_service import ProjectService
        
        file_service = FileService()
        project_service = ProjectService()
        comparison_service = ComparisonService(None) # Repo set later
        
        view = FolderComparisonApp(root)
        controller = AppController(view, file_service, comparison_service, project_service)
        
        # Connect comparison service to project service's repository
        # This is a bit circular, but we'll fix it by having controller update it
        
        root.mainloop()
    except tk.TclError as e:
        logging.error("Could not start GUI. Is a display available?", exc_info=True)
    except Exception as e:
        logging.critical("Application crashed with an unhandled exception.", exc_info=True)
        # Optionally, show a simple error message to the user before exiting
        tk.messagebox.showerror("Fatal Error", "A critical error occurred. Please check the logs for details.")
