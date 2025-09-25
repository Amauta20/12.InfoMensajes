import sqlite3
import os

# Define the path for the database in the project root
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "infomensajero.db")

def get_db_connection():
    """Creates a database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def create_schema():
    """Creates the database schema if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for services
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        icon TEXT,
        profile_path TEXT NOT NULL UNIQUE,
        is_active BOOLEAN DEFAULT 1
    );
    """)

    # Table for notes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tables for Kanban board
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kanban_columns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        position INTEGER NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kanban_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        column_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        finished_at TIMESTAMP,
        FOREIGN KEY (column_id) REFERENCES kanban_columns (id)
    );
    """)

    # FTS5 virtual table for message indexing
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS messages_index USING fts5(
        source, 
        thread_id, 
        author, 
        snippet, 
        content, 
        created_at
    );
    """)

    # Table for encrypted credentials (vault)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS credentials (
        id TEXT PRIMARY KEY,
        enc_blob BLOB NOT NULL,
        nonce BLOB NOT NULL,
        salt BLOB NOT NULL
    );
    """)

    # Table for usage metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usage_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        milliseconds INTEGER NOT NULL,
        day TEXT NOT NULL, -- YYYY-MM-DD
        FOREIGN KEY (service_id) REFERENCES services (id)
    );
    """)

    # Table for application settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()
    print("Database schema created successfully.")

if __name__ == '__main__':
    create_schema()
