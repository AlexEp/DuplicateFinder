from ..base_database import BaseDatabase

class HistogramDatabase(BaseDatabase):
    def get_table_name(self, method):
        """
        Returns the table name for the given histogram method.
        """
        method_map = {
            'Correlation': 'histogram_correlation',
            'Chi-Square': 'histogram_chisqr',
            'Intersection': 'histogram_intersection',
            'Bhattacharyya': 'histogram_bhattacharyya'
        }
        return method_map.get(method)

    def save(self, conn, file_id, data, method):
        """
        Saves the histogram of a file to the database.
        """
        table_name = self.get_table_name(method)
        with conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {table_name} (file_id, histogram_values) VALUES (?, ?)",
                (file_id, data)
            )

    def load(self, conn, file_id, method):
        """
        Loads the histogram of a file from the database.
        """
        table_name = self.get_table_name(method)
        cursor = conn.cursor()
        cursor.execute(f"SELECT histogram_values FROM {table_name} WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        return row[0] if row else None
