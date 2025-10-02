from app.db.database import get_db_connection
import datetime
from app.utils import time_utils

def create_checklist(name, kanban_card_id=None):
    """Creates a new checklist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO checklists (name, kanban_card_id) VALUES (?, ?)",
        (name, kanban_card_id)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def _process_checklist_join_results(rows):
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
        
        item_id = row['item_id']
        if item_id: # Only add item if it exists
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

def get_all_checklists():
    """Retrieves all checklists with their items using a single JOIN query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.id, c.name, c.kanban_card_id,
            ci.id AS item_id, ci.text AS item_text, ci.is_checked, ci.due_at AS item_due_at, ci.is_notified AS item_is_notified, ci.pre_notified_at AS item_pre_notified_at
        FROM checklists c
        LEFT JOIN checklist_items ci ON c.id = ci.checklist_id
        ORDER BY c.id DESC, ci.id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return _process_checklist_join_results(rows)

def get_checklist(checklist_id):
    """Retrieves a single checklist with its items using a single JOIN query."""
    conn = get_db_connection()
    cursor = conn.cursor()
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
    conn.close()
    if rows:
        return _process_checklist_join_results(rows)[0]
    return None

def update_checklist_name(checklist_id, new_name):
    """Updates the name of a checklist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE checklists SET name = ? WHERE id = ?", (new_name, checklist_id))
    conn.commit()
    conn.close()

def delete_checklist(checklist_id):
    """Deletes a checklist and all its items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM checklists WHERE id = ?", (checklist_id,))
    conn.commit()
    conn.close()

def add_item_to_checklist(checklist_id, text, due_at=None):
    """Adds a new item to a checklist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    due_at_utc_str = time_utils.to_utc(due_at).isoformat() if isinstance(due_at, datetime.datetime) else due_at
    cursor.execute(
        "INSERT INTO checklist_items (checklist_id, text, due_at) VALUES (?, ?, ?)",
        (checklist_id, text, due_at_utc_str)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_checklist_item(item_id, text=None, is_checked=None, due_at=None, is_notified=None, pre_notified_at=None):
    """Updates a checklist item's text, checked state, due date, or notification status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if text is not None:
        cursor.execute("UPDATE checklist_items SET text = ? WHERE id = ?", (text, item_id))
    if is_checked is not None:
        cursor.execute("UPDATE checklist_items SET is_checked = ? WHERE id = ?", (is_checked, item_id))
    if due_at is not None:
        due_at_utc_str = time_utils.to_utc(due_at).isoformat() if isinstance(due_at, datetime.datetime) else due_at
        cursor.execute("UPDATE checklist_items SET due_at = ? WHERE id = ?", (due_at_utc_str, item_id))
    if is_notified is not None:
        cursor.execute("UPDATE checklist_items SET is_notified = ? WHERE id = ?", (is_notified, item_id))
    if pre_notified_at is not None:
        pre_notified_at_utc_str = time_utils.to_utc(pre_notified_at).isoformat() if isinstance(pre_notified_at, datetime.datetime) else pre_notified_at
        cursor.execute("UPDATE checklist_items SET pre_notified_at = ? WHERE id = ?", (pre_notified_at_utc_str, item_id))
    conn.commit()
    conn.close()

def delete_checklist_item(item_id):
    """Deletes a checklist item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM checklist_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def get_actual_due_checklist_items():
    """Retrieves all due and not notified checklist items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_utc = time_utils.to_utc(datetime.datetime.now()).isoformat()
    cursor.execute("SELECT id, text, checklist_id, due_at, pre_notified_at FROM checklist_items WHERE due_at <= ? AND is_checked = 0 AND is_notified = 0", (now_utc,))
    items = []
    for row in cursor.fetchall():
        item = dict(row)
        if item['due_at']:
            utc_dt = datetime.datetime.fromisoformat(item['due_at'])
            item['due_at'] = time_utils.from_utc(utc_dt).isoformat()
        items.append(item)
    conn.close()
    return items

def get_pre_due_checklist_items(pre_notification_offset_minutes):
    """Retrieves checklist items that are due within the pre-notification offset and have not been pre-notified."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now()
    now_utc = time_utils.to_utc(now)
    pre_due_time_utc = now_utc + datetime.timedelta(minutes=pre_notification_offset_minutes)

    now_str = now_utc.isoformat()
    pre_due_time_str = pre_due_time_utc.isoformat()

    cursor.execute("SELECT id, text, checklist_id, due_at FROM checklist_items WHERE due_at > ? AND due_at <= ? AND is_checked = 0 AND pre_notified_at IS NULL", (now_str, pre_due_time_str))
    items = []
    for row in cursor.fetchall():
        item = dict(row)
        if item['due_at']:
            utc_dt = datetime.datetime.fromisoformat(item['due_at'])
            item['due_at'] = time_utils.from_utc(utc_dt).isoformat()
        items.append(item)
    conn.close()
    return items



def get_checklists_for_card(kanban_card_id):
    """Retrieves all checklists for a given Kanban card with their items using a single JOIN query."""
    conn = get_db_connection()
    cursor = conn.cursor()
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
    conn.close()
    return _process_checklist_join_results(rows)

def get_independent_checklists():
    """Retrieves all checklists that are not associated with a Kanban card with their items using a single JOIN query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.id, c.name, c.kanban_card_id,
            ci.id AS item_id, ci.text AS item_text, ci.is_checked, ci.due_at AS item_due_at, ci.is_notified AS item_is_notified, ci.pre_notified_at AS item_pre_notified_at
        FROM checklists c
        LEFT JOIN checklist_items ci ON c.id = ci.checklist_id
        WHERE c.kanban_card_id IS NULL
        ORDER BY c.id DESC, ci.id ASC
    """
    )
    rows = cursor.fetchall()
    conn.close()
    return _process_checklist_join_results(rows)

def get_items_due_between(start_date, end_date):
    """Retrieves checklist items with a due date between the given dates."""
    conn = get_db_connection()
    items = conn.execute("SELECT text, due_at FROM checklist_items WHERE due_at BETWEEN ? AND ?", (start_date, end_date)).fetchall()
    conn.close()
    return items
