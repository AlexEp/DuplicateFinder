from ..base_database import BaseDatabase

class MD5Database(BaseDatabase):
    def save(self, conn, file_id, data):
        """
        Saves the MD5 hash of a file to the database.
        """
        with conn:
            conn.execute(
                "UPDATE file_metadata SET md5 = ? WHERE file_id = ?",
                (data, file_id)
            )

    def load(self, conn, file_id):
        """
        Loads the MD5 hash of a file from the database.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT md5 FROM file_metadata WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        return row[0] if row else None
