import datetime
from app.db.database import get_db_connection
from app.utils import time_utils

def create_note(db_path, content):
    """Adds a new note to the database."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    current_utc_time = time_utils.to_utc(datetime.datetime.now()).isoformat()
    cursor.execute("INSERT INTO notes (content, created_at) VALUES (?, ?)", (content, current_utc_time))
    conn.commit()
    note_id = cursor.lastrowid
    return note_id

def get_all_notes(db_path):
    """Retrieves all notes from the database, newest first."""
    conn = get_db_connection(db_path)
    notes = conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
    conn.close()
    return notes

def delete_note(db_path, note_id):
    """Deletes a note from the database."""
    conn = get_db_connection(db_path)
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

def update_note(db_path, note_id, new_content):
    """Updates the content of an existing note."""
    conn = get_db_connection(db_path)
    conn.execute("UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_content, note_id))
    conn.commit()
    conn.close()
