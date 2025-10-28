import datetime
from app.utils import time_utils

class NotesManager:
    def __init__(self, conn):
        self.conn = conn

    def create_note(self, content):
        """Adds a new note to the database."""
        cursor = self.conn.cursor()
        current_utc_time = time_utils.to_utc(datetime.datetime.now()).isoformat()
        cursor.execute("INSERT INTO notes (content, created_at) VALUES (?, ?)", (content, current_utc_time))
        self.conn.commit()
        note_id = cursor.lastrowid
        return note_id

    def get_all_notes(self):
        """Retrieves all notes from the database, newest first."""
        notes = self.conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
        return notes

    def delete_note(self, note_id):
        """Deletes a note from the database."""
        self.conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()

    def update_note(self, note_id, new_content):
        """Updates the content of an existing note."""
        self.conn.execute("UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_content, note_id))
        self.conn.commit()
