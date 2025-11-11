from app.db.notes_manager import NotesManager

class NotesService:
    """
    A service layer for handling business logic related to notes.
    It decouples the UI from the data access layer.
    """
    def __init__(self, notes_manager: NotesManager):
        self.notes_manager = notes_manager

    def get_all_notes(self):
        """Retrieves all notes."""
        return self.notes_manager.get_all_notes()

    def create_note(self, content: str):
        """Adds a new note."""
        return self.notes_manager.create_note(content)

    def update_note(self, note_id: int, new_content: str):
        """Updates an existing note."""
        self.notes_manager.update_note(note_id, new_content)

    def delete_note(self, note_id: int):
        """Deletes a note."""
        self.notes_manager.delete_note(note_id)
