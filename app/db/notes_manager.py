from app.db.database import get_db_connection

def create_note(content):
    """Adds a new note to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return note_id

def get_all_notes():
    """Retrieves all notes from the database, newest first."""
    conn = get_db_connection()
    notes = conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
    conn.close()
    return notes

def delete_note(note_id):
    """Deletes a note from the database."""
    conn = get_db_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

def update_note(note_id, new_content):
    """Updates the content of an existing note."""
    conn = get_db_connection()
    conn.execute("UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_content, note_id))
    conn.commit()
    conn.close()
