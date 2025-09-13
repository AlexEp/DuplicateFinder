from ..base_database import BaseDatabase
import logging

logger = logging.getLogger(__name__)

class IntersectionHistogramDatabase(BaseDatabase):
    def get_table_name(self):
        """
        Returns the table name for the intersection histogram.
        """
        return 'histogram_intersection'

    def save(self, conn, file_id, data):
        """
        Saves the histogram of a file to the database.
        """
        table_name = self.get_table_name()
        logger.info(f"Saving histogram for file_id {file_id} to table {table_name}")
        with conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {table_name} (file_id, histogram_values) VALUES (?, ?)",
                (file_id, data)
            )

    def load(self, conn, file_id):
        """
        Loads the histogram of a file from the database.
        """
        table_name = self.get_table_name()
        cursor = conn.cursor()
        cursor.execute(f"SELECT histogram_values FROM {table_name} WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        return row[0] if row else None
