import sqlite3
import time
import json
import logging
import threading
import queue
from pathlib import Path

logger = logging.getLogger(__name__)

class MetricCache:
    """
    Local SQLite-based cache for file calculation metrics.
    Keeps computed metrics for a defined duration (default 30 mins) based on
    the composite key: (file_path, file_size, metric_name).
    """
    _instance = None
    
    def __new__(cls, db_path="metric_cache.db"):
        if cls._instance is None:
            cls._instance = super(MetricCache, cls).__new__(cls)
            cls._instance._init_db(db_path)
        return cls._instance

    def _init_db(self, db_path):
        self.db_path = Path(db_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    file_path TEXT,
                    file_size INTEGER,
                    metric_name TEXT,
                    metric_value TEXT,
                    timestamp REAL,
                    PRIMARY KEY (file_path, file_size, metric_name)
                )
            """)

        self._write_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._worker_thread.start()

    def _writer_loop(self):
        """Background thread loop that pulls from the queue and writes to SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            while True:
                try:
                    item = self._write_queue.get()
                    if item is None:  # Shutdown signal
                        break
                        
                    file_path, file_size, metric_name, serialized_val, current_time = item
                    
                    try:
                        conn.execute(
                            """
                            INSERT INTO metrics (file_path, file_size, metric_name, metric_value, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(file_path, file_size, metric_name) DO UPDATE SET
                            metric_value = excluded.metric_value,
                            timestamp = excluded.timestamp
                            """,
                            (file_path, file_size, metric_name, serialized_val, current_time)
                        )
                        conn.commit()
                    except sqlite3.Error as e:
                        logger.error(f"Error writing to metric cache: {e}")
                        
                    self._write_queue.task_done()
                except Exception as e:
                    logger.error(f"Unexpected error in metric cache writer loop: {e}")

    def wait_for_writes(self):
        """Blocks until all queued cache writes are processed."""
        self._write_queue.join()

    def clean_old_cache(self, max_age_minutes=30):
        """Deletes cache entries older than the maximum age."""
        cutoff_time = time.time() - (max_age_minutes * 60)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_time,))
                deleted = cursor.rowcount
                if deleted > 0:
                    logger.debug(f"Cleared {deleted} old metric cache entries.")
        except sqlite3.Error as e:
            logger.error(f"Error cleaning metric cache: {e}")

    def get_metric(self, file_path, file_size, metric_name):
        """
        Retrieves a metric from the cache. 
        If found, updates its timestamp and returns the deserialized value.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT metric_value FROM metrics WHERE file_path = ? AND file_size = ? AND metric_name = ?",
                    (file_path, file_size, metric_name)
                )
                row = cursor.fetchone()
                
                if row:
                    # Update timestamp to keep it alive
                    current_time = time.time()
                    conn.execute(
                        "UPDATE metrics SET timestamp = ? WHERE file_path = ? AND file_size = ? AND metric_name = ?",
                        (current_time, file_path, file_size, metric_name)
                    )
                    
                    # Deserialize
                    serialized_val = row[0]
                    return json.loads(serialized_val)
                    
        except sqlite3.Error as e:
            logger.error(f"Error reading from metric cache: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding cached metric for {metric_name} on {file_path}: {e}")
            
        return None

    def set_metric(self, file_path, file_size, metric_name, value):
        """
        Asynchronously saves a newly calculated metric into the cache.
        """
        if value is None:
            return # Don't cache Nones
            
        try:
            # Serialize synchronously since we want to catch JSON errors on the calling thread
            serialized_val = json.dumps(value)
            current_time = time.time()
            
            # Offload the database write
            self._write_queue.put((file_path, file_size, metric_name, serialized_val, current_time))
            
        except TypeError as e:
            logger.error(f"Error encoding metric for {metric_name} on {file_path}: {e}")
