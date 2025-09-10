import sqlite3
import json
from models import FileNode, FolderNode

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
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE
            )
        """
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_index INTEGER,
                path TEXT,
                name TEXT,
                ext TEXT,
                last_seen REAL,
                FOREIGN KEY (folder_index) REFERENCES sources (id)
            )
        """
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER UNIQUE,
                size INTEGER,
                modified_date REAL,
                md5 TEXT,
                histogram TEXT,
                llm_embedding BLOB,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """
        )
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_files_path_folder ON files (folder_index, path, name)")

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

def delete_file_by_path(conn, path, name):
    with conn:
        conn.execute("DELETE FROM files WHERE path = ? AND name = ?", (path, name))

def insert_file_node(conn, node, folder_index, current_folder_path=''):
    if isinstance(node, FileNode):
        with conn:
            cursor = conn.execute("""
                INSERT INTO files (folder_index, path, name, ext, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (folder_index, current_folder_path, node.name, node.ext, node.metadata.get('last_seen')))
            file_id = cursor.lastrowid
            conn.execute("""
                INSERT INTO file_metadata (file_id, size, modified_date, md5, histogram, llm_embedding)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, node.metadata.get('size'), node.metadata.get('date'), node.metadata.get('md5'), node.metadata.get('histogram'), node.metadata.get('llm_embedding')))
    elif isinstance(node, FolderNode):
        new_folder_path = f"{current_folder_path}/{node.name}" if current_folder_path else node.name
        for child in node.content:
            insert_file_node(conn, child, folder_index, new_folder_path)

def get_all_files(conn, folder_index):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            f.id, f.folder_index, f.path, f.name, f.ext, f.last_seen,
            fm.size, fm.modified_date, fm.md5, fm.histogram, fm.llm_embedding
        FROM
            files f
        LEFT JOIN
            file_metadata fm ON f.id = fm.file_id
        WHERE
            f.folder_index = ?
    """, (folder_index,))
    return cursor.fetchall()

def get_files_by_ids(conn, ids):
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in ids)
    query = f"""
        SELECT
            f.id, f.folder_index, f.path, f.name, f.ext, f.last_seen,
            fm.size, fm.modified_date, fm.md5, fm.histogram, fm.llm_embedding
        FROM
            files f
        LEFT JOIN
            file_metadata fm ON f.id = fm.file_id
        WHERE
            f.id IN ({placeholders})
    """
    cursor.execute(query, ids)
    return cursor.fetchall()

def add_source(conn, path):
    with conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sources (path) VALUES (?)", (path,))
        return cursor.lastrowid

def get_sources(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM sources ORDER BY id")
    return cursor.fetchall()

def clear_sources(conn):
    with conn:
        conn.execute("DELETE FROM sources")