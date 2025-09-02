import logging
import os
from datetime import datetime
from config import config

def setup_logging():
    """
    Sets up logging for the application.

    Reads the log level from the central config, creates a 'logs' directory
    if it doesn't exist, and configures a logger to write to a file named
    YYYYMMDD.log within that directory.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")

    log_level = config.get("log_level", "INFO").upper()

    # Get the numeric value for the log level
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler() # Also log to console
        ]
    )

    # Log the successful setup
    logging.info(f"Logging initialized with level {log_level}.")
