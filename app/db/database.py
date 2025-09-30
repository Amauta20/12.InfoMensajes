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
        assignee TEXT,
        due_date TIMESTAMP,
        FOREIGN KEY (column_id) REFERENCES kanban_columns (id)
    );
    """)

    # Add new columns to kanban_cards if they don't exist
    cursor.execute("PRAGMA table_info(kanban_cards);")
    columns = [col[1] for col in cursor.fetchall()]
    if 'assignee' not in columns:
        cursor.execute("ALTER TABLE kanban_cards ADD COLUMN assignee TEXT;")
    if 'due_date' not in columns:
        cursor.execute("ALTER TABLE kanban_cards ADD COLUMN due_date TIMESTAMP;")

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

    # Tables for checklists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        kanban_card_id INTEGER,
        FOREIGN KEY (kanban_card_id) REFERENCES kanban_cards (id) ON DELETE SET NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS checklist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checklist_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        is_checked INTEGER NOT NULL DEFAULT 0,
        due_at TIMESTAMP,
        is_notified INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (checklist_id) REFERENCES checklists (id) ON DELETE CASCADE
    );
    """)

    # Add due_at column to checklist_items if it doesn't exist
    cursor.execute("PRAGMA table_info(checklist_items);")
    columns = [col[1] for col in cursor.fetchall()]
    if 'due_at' not in columns:
        cursor.execute("ALTER TABLE checklist_items ADD COLUMN due_at TIMESTAMP;")
    if 'is_notified' not in columns:
        cursor.execute("ALTER TABLE checklist_items ADD COLUMN is_notified INTEGER NOT NULL DEFAULT 0;")
    if 'pre_notified_at' not in columns:
        cursor.execute("ALTER TABLE checklist_items ADD COLUMN pre_notified_at TIMESTAMP;")

    # Table for reminders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        due_at TIMESTAMP NOT NULL,
        is_completed INTEGER NOT NULL DEFAULT 0
    );
    """)

    # Add is_notified column to reminders if it doesn't exist
    cursor.execute("PRAGMA table_info(reminders);")
    columns = [col[1] for col in cursor.fetchall()]
    if 'is_notified' not in columns:
        cursor.execute("ALTER TABLE reminders ADD COLUMN is_notified INTEGER NOT NULL DEFAULT 0;")
    if 'pre_notified_at' not in columns:
        cursor.execute("ALTER TABLE reminders ADD COLUMN pre_notified_at TIMESTAMP;")

    # Table for RSS feeds
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rss_feeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE
    );
    """)

    conn.commit()
    conn.close()
    print("Database schema created successfully.")

if __name__ == '__main__':
    create_schema()
