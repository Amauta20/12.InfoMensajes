import sqlite3
import os
from pathlib import Path

import sys

# Path to the SQLite database file
if getattr(sys, 'frozen', False):
    # Production mode: Use AppData
    app_data_dir = os.path.join(os.getenv('APPDATA'), 'InfoMensajero')
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)
    DB_FILE = Path(app_data_dir) / 'database.db'
else:
    # Development mode: Use project root
    DB_FILE = Path(__file__).resolve().parent.parent.parent / 'database.db'

def get_db_connection(db_file_path: str | None = None) -> sqlite3.Connection:
    """Create and return a SQLite connection.

    If *db_file_path* is provided it overrides the default location.
    The connection uses ``sqlite3.Row`` for dict‑like access and enables
    foreign‑key support.
    """
    path_to_use = Path(db_file_path) if db_file_path else DB_FILE
    # check_same_thread=False allows using the connection in multiple threads.
    # With WAL mode enabled, this is safer, but we should still be careful.
    conn = sqlite3.connect(path_to_use, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def create_schema(existing_conn: sqlite3.Connection | None = None) -> None:
    """Create the full database schema if it does not exist.

    The function is idempotent – it uses ``IF NOT EXISTS`` for all objects.
    When *existing_conn* is supplied the caller manages the connection
    lifecycle; otherwise a temporary connection is created and closed.
    """
    conn = existing_conn or get_db_connection()
    try:
        cursor = conn.cursor()

        # -----------------------------------------------------------------
        # Core tables
        # -----------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                icon TEXT,
                profile_path TEXT NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT 1,
                is_internal BOOLEAN DEFAULT 0,
                unread_script TEXT
            );
            """
        )
        # Ensure columns exist (migration safety)
        cursor.execute("PRAGMA table_info(services);")
        cols = {c[1] for c in cursor.fetchall()}
        if "is_internal" not in cols:
            cursor.execute("ALTER TABLE services ADD COLUMN is_internal BOOLEAN DEFAULT 0;")
        if "unread_script" not in cols:
            cursor.execute("ALTER TABLE services ADD COLUMN unread_script TEXT;")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )

        # -----------------------------------------------------------------
        # Kanban board tables
        # -----------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS kanban_columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                position INTEGER NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS kanban_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                column_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                started_at TEXT,
                finished_at TEXT,
                assignee TEXT,
                due_date TEXT,
                start_date TEXT,
                end_date TEXT,
                FOREIGN KEY (column_id) REFERENCES kanban_columns (id) ON DELETE CASCADE
            );
            """
        )
        # Migration for new columns
        cursor.execute("PRAGMA table_info(kanban_cards);")
        kc_cols = {c[1] for c in cursor.fetchall()}
        for col in ["assignee", "due_date", "start_date", "end_date"]:
            if col not in kc_cols:
                cursor.execute(f"ALTER TABLE kanban_cards ADD COLUMN {col} TEXT;")

        # -----------------------------------------------------------------
        # Full‑text search virtual tables and triggers
        # -----------------------------------------------------------------
        cursor.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(content, tokenize='porter unicode61');"
        )
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS notes_after_insert AFTER INSERT ON notes BEGIN
                INSERT INTO notes_fts(rowid, content) VALUES (new.id, COALESCE(new.content, ''));
            END;
            """
        )
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS notes_after_delete AFTER DELETE ON notes BEGIN
                DELETE FROM notes_fts WHERE rowid = old.id;
            END;
            """
        )
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS notes_after_update AFTER UPDATE ON notes BEGIN
                DELETE FROM notes_fts WHERE rowid = old.id;
                INSERT INTO notes_fts(rowid, content) VALUES (new.id, COALESCE(new.content, ''));
            END;
            """
        )

        cursor.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS kanban_cards_fts USING fts5(title, description, tokenize='porter unicode61');"
        )
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS kanban_cards_after_insert AFTER INSERT ON kanban_cards BEGIN
                INSERT INTO kanban_cards_fts(rowid, title, description) VALUES (new.id, COALESCE(new.title, ''), COALESCE(new.description, ''));
            END;
            """
        )

        # -----------------------------------------------------------------
        # Security / Vault tables
        # -----------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS credentials (
                id TEXT PRIMARY KEY,
                enc_blob BLOB NOT NULL,
                nonce BLOB NOT NULL,
                salt BLOB NOT NULL
            );
            """
        )

        # -----------------------------------------------------------------
        # Metrics and settings
        # -----------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                milliseconds INTEGER NOT NULL,
                day TEXT NOT NULL,
                FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )

        # -----------------------------------------------------------------
        # Checklists and reminders
        # -----------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                kanban_card_id INTEGER,
                FOREIGN KEY (kanban_card_id) REFERENCES kanban_cards (id) ON DELETE CASCADE
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS checklist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checklist_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                is_checked INTEGER NOT NULL DEFAULT 0,
                due_at TEXT,
                is_notified INTEGER NOT NULL DEFAULT 0,
                pre_notified_at TEXT,
                FOREIGN KEY (checklist_id) REFERENCES checklists (id) ON DELETE CASCADE
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                due_at TEXT NOT NULL,
                is_completed INTEGER NOT NULL DEFAULT 0,
                is_notified INTEGER NOT NULL DEFAULT 0,
                pre_notified_at TEXT
            );
            """
        )

        # -----------------------------------------------------------------
        # RSS feeds
        # -----------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rss_feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE
            );
            """
        )

        # -----------------------------------------------------------------
        # Automation: Rules and Templates (Phase 3)
        # -----------------------------------------------------------------
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_params TEXT,  -- JSON payload
                is_active BOOLEAN DEFAULT 1
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                created_at TEXT NOT NULL
            );
            """
        )

        # -----------------------------------------------------------------
        # Indexes for performance (optional but recommended)
        # -----------------------------------------------------------------
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanban_cards_column_id ON kanban_cards(column_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_checklists_kanban_card_id ON checklists(kanban_card_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_checklist_items_checklist_id ON checklist_items(checklist_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_metrics_service_id ON usage_metrics(service_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due_at ON reminders(due_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_checklist_items_due_at ON checklist_items(due_at);")

        conn.commit()
    finally:
        if not existing_conn:
            conn.close()
            print("Database schema created successfully.")

if __name__ == '__main__':
    create_schema()
