from ..base_database import BaseDatabase

class DateDatabase(BaseDatabase):
    def save(self, conn, file_id, data):
        """
        Saves the modification date of a file to the database.
        """
        with conn:
            conn.execute(
                "UPDATE file_metadata SET modified_date = ? WHERE file_id = ?",
                (data, file_id)
            )

    def load(self, conn, file_id):
        """
        Loads the modification date of a file from the database.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT modified_date FROM file_metadata WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    