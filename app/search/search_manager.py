import sqlite3
from app.db.database import get_db_connection

def index_text(source, content, thread_id=None, author=None, snippet=None):
    """Adds text content to the FTS5 index."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages_index (source, thread_id, author, snippet, content) VALUES (?, ?, ?, ?, ?)",
        (source, thread_id, author, snippet, content)
    )
    conn.commit()
    conn.close()

def search_all(query):
    """Searches across notes, kanban cards, and the messages_index FTS5 table."""
    conn = get_db_connection()
    results = []
    like_query = f"%{query}%"

    # Search notes
    notes = conn.execute(
        "SELECT 'note' as type, id, content FROM notes WHERE content LIKE ?",
        (like_query,)
    ).fetchall()
    results.extend(notes)

    # Search kanban cards (title and description)
    kanban_cards = conn.execute(
        "SELECT 'kanban_card' as type, id, title, description FROM kanban_cards WHERE title LIKE ? OR description LIKE ?",
        (like_query, like_query)
    ).fetchall()
    results.extend(kanban_cards)

    # Search messages_index
    messages = conn.execute(
        "SELECT 'message' as type, source, thread_id, author, snippet, content FROM messages_index WHERE content MATCH ?",
        (query,)
    ).fetchall()
    results.extend(messages)

    conn.close()
    return results
