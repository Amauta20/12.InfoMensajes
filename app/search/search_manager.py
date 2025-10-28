import sqlite3

class SearchManager:
    def __init__(self, conn):
        self.conn = conn

    def rebuild_fts_indexes(self):
        """Rebuilds the FTS indexes to ensure they are up to date with existing data."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO notes_fts(notes_fts) VALUES('rebuild');")
            cursor.execute("INSERT INTO kanban_cards_fts(kanban_cards_fts) VALUES('rebuild');")
            self.conn.commit()
            print("FTS indexes rebuilt successfully.")
        except Exception as e:
            print(f"Error rebuilding FTS indexes: {e}")
        # No conn.close() here, as connection is managed externally

    def search_all(self, query):
        """Searches across notes and kanban cards using FTS5."""
        results = []
        
        # FTS query requires a specific format, add wildcards for prefix search
        fts_query = f'{query}*'

        # Search notes_fts
        # We use a JOIN to get the original note content for display
        notes_query = """
            SELECT 
                'note' as type, 
                n.id, 
                n.content 
            FROM notes n
            JOIN notes_fts fts ON n.id = fts.rowid
            WHERE fts.notes_fts MATCH ?
        """
        notes = self.conn.execute(notes_query, (fts_query,)).fetchall()
        results.extend(notes)

        # Search kanban_cards_fts
        kanban_query = """
            SELECT 
                'kanban_card' as type, 
                k.id, 
                k.title, 
                k.description
            FROM kanban_cards k
            JOIN kanban_cards_fts fts ON k.id = fts.rowid
            WHERE fts.kanban_cards_fts MATCH ?
        """
        kanban_cards = self.conn.execute(kanban_query, (fts_query,)).fetchall()
        results.extend(kanban_cards)

        return results
