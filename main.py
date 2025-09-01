import tkinter as tk
import logging
from ui import FolderComparisonApp
from logger_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    try:
        root = tk.Tk()
        app = FolderComparisonApp(root)
        root.mainloop()
    except Exception as e:
        logging.critical("Application crashed with an unhandled exception.", exc_info=True)
        # Optionally, show a simple error message to the user before exiting
        tk.messagebox.showerror("Fatal Error", "A critical error occurred. Please check the logs for details.")
