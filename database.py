
import sqlite3
import json
from models import FileNode

def get_db_connection(project_file):
    return sqlite3.connect(project_file)

def create_tables(conn):
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_index INTEGER,
                relative_path TEXT,
                name TEXT,
                ext TEXT,
                size INTEGER,
                modified_date REAL,
                md5 TEXT,
                histogram TEXT,
                llm_embedding BLOB
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_files_path_folder ON files (folder_index, relative_path)")

def save_setting(conn, key, value):
    with conn:
        conn.execute("INSERT OR REPLACE INTO project_settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))

def load_setting(conn, key):
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM project_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return json.loads(row[0]) if row else None

def clear_folder_data(conn, folder_index):
    with conn:
        conn.execute("DELETE FROM files WHERE folder_index = ?", (folder_index,))

def insert_file_node(conn, node, folder_index):
    """
    Inserts a single FileNode into the database. Used for testing.
    The main application uses bulk inserts via build_folder_structure_db.
    """
    if isinstance(node, FileNode):
        try:
            stat = node.path_obj.stat()
            size = stat.st_size
            modified_date = stat.st_mtime
        except (OSError, AttributeError):
            # If it's a mock object or path doesn't exist, use defaults
            size = 0
            modified_date = 0

        with conn:
            conn.execute("""
                INSERT INTO files (folder_index, relative_path, name, ext, size, modified_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (folder_index, node.relative_path, node.name, node.ext, size, modified_date))

def get_all_files(conn, folder_index):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE folder_index = ?", (folder_index,))
    return cursor.fetchall()
