import datetime
from app.utils import time_utils

class ChecklistManager:
    def __init__(self, conn):
        self.conn = conn

    def create_checklist(self, name, kanban_card_id=None):
        """Creates a new checklist."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO checklists (name, kanban_card_id) VALUES (?, ?)",
            (name, kanban_card_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def _process_checklist_join_results(self, rows):
        checklists = {}
        for row in rows:
            checklist_id = row['id']
            if checklist_id not in checklists:
                checklists[checklist_id] = {
                    'id': row['id'],
                    'name': row['name'],
                    'kanban_card_id': row['kanban_card_id'],
                    'items': []
                }
            
            if row['item_id']:
                item = {
                    'id': row['item_id'],
                    'text': row['item_text'],
                    'is_checked': row['is_checked'],
                    'due_at': row['item_due_at'],
                    'is_notified': row['item_is_notified'],
                    'pre_notified_at': row['item_pre_notified_at']
                }
                checklists[checklist_id]['items'].append(item)
        return list(checklists.values())

    def get_all_checklists(self):
        """Retrieves all checklists with their items."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                c.id, c.name, c.kanban_card_id,
                ci.id AS item_id, ci.text AS item_text, ci.is_checked, ci.due_at AS item_due_at, ci.is_notified AS item_is_notified, ci.pre_notified_at AS item_pre_notified_at
            FROM checklists c
            LEFT JOIN checklist_items ci ON c.id = ci.checklist_id
            ORDER BY c.id DESC, ci.id ASC
        """)
        rows = cursor.fetchall()
        return self._process_checklist_join_results(rows)

    def get_checklist(self, checklist_id):
        """Retrieves a single checklist with its items."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                c.id, c.name, c.kanban_card_id,
                ci.id AS item_id, ci.text AS item_text, ci.is_checked, ci.due_at AS item_due_at, ci.is_notified AS item_is_notified, ci.pre_notified_at AS item_pre_notified_at
            FROM checklists c
            LEFT JOIN checklist_items ci ON c.id = ci.checklist_id
            WHERE c.id = ?
            ORDER BY ci.id ASC
        """, (checklist_id,))
        rows = cursor.fetchall()
        if rows:
            processed_results = self._process_checklist_join_results(rows)
            return processed_results[0] if processed_results else None
        return None

    def update_checklist_name(self, checklist_id, new_name):
        """Updates the name of a checklist."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE checklists SET name = ? WHERE id = ?", (new_name, checklist_id))
        self.conn.commit()

    def delete_checklist(self, checklist_id):
        """Deletes a checklist and all its items."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM checklists WHERE id = ?", (checklist_id,))
        self.conn.commit()

    def add_item_to_checklist(self, checklist_id, text, due_at=None):
        """Adds a new item to a checklist."""
        cursor = self.conn.cursor()
        due_at_utc_str = time_utils.to_utc(due_at).isoformat() if isinstance(due_at, datetime.datetime) else due_at
        cursor.execute(
            "INSERT INTO checklist_items (checklist_id, text, due_at) VALUES (?, ?, ?)",
            (checklist_id, text, due_at_utc_str)
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_checklist_item(self, item_id, text=None, is_checked=None, due_at=None, is_notified=None, pre_notified_at=None):
        """Updates a checklist item."""
        cursor = self.conn.cursor()
        updates = []
        params = []
        if text is not None:
            updates.append("text = ?")
            params.append(text)
        if is_checked is not None:
            updates.append("is_checked = ?")
            params.append(is_checked)
        if due_at is not None:
            due_at_utc_str = time_utils.to_utc(due_at).isoformat() if isinstance(due_at, datetime.datetime) else due_at
            updates.append("due_at = ?")
            params.append(due_at_utc_str)
        if is_notified is not None:
            updates.append("is_notified = ?")
            params.append(is_notified)
        if pre_notified_at is not None:
            pre_notified_at_utc_str = time_utils.to_utc(pre_notified_at).isoformat() if isinstance(pre_notified_at, datetime.datetime) else pre_notified_at
            updates.append("pre_notified_at = ?")
            params.append(pre_notified_at_utc_str)

        if updates:
            params.append(item_id)
            cursor.execute(f"UPDATE checklist_items SET {', '.join(updates)} WHERE id = ?", tuple(params))
            self.conn.commit()

    def delete_checklist_item(self, item_id):
        """Deletes a checklist item."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM checklist_items WHERE id = ?", (item_id,))
        self.conn.commit()

    def get_checklist_item(self, item_id):
        """Retrieves a single checklist item."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM checklist_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_checklists_for_card(self, kanban_card_id):
        """Retrieves all checklists for a given Kanban card."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                c.id, c.name, c.kanban_card_id,
                ci.id AS item_id, ci.text AS item_text, ci.is_checked, ci.due_at AS item_due_at, ci.is_notified AS item_is_notified, ci.pre_notified_at AS item_pre_notified_at
            FROM checklists c
            LEFT JOIN checklist_items ci ON c.id = ci.checklist_id
            WHERE c.kanban_card_id = ?
            ORDER BY c.id DESC, ci.id ASC
        """, (kanban_card_id,))
        rows = cursor.fetchall()
        return self._process_checklist_join_results(rows)

    def get_independent_checklists(self):
        """Retrieves all checklists not associated with a Kanban card."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                c.id, c.name, c.kanban_card_id,
                ci.id AS item_id, ci.text AS item_text, ci.is_checked, ci.due_at AS item_due_at, ci.is_notified AS item_is_notified, ci.pre_notified_at AS item_pre_notified_at
            FROM checklists c
            LEFT JOIN checklist_items ci ON c.id = ci.checklist_id
            WHERE c.kanban_card_id IS NULL
            ORDER BY c.id DESC, ci.id ASC
        """)
        rows = cursor.fetchall()
        return self._process_checklist_join_results(rows)