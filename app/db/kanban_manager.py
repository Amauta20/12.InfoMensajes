import sqlite3
from app.db.database import get_db_connection
import datetime
from app.utils import time_utils

def create_default_columns():
    """Ensures the default Kanban columns exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    default_columns = [("Por Hacer", 0), ("En Progreso", 1), ("Realizadas", 2)]
    for name, position in default_columns:
        cursor.execute("INSERT OR IGNORE INTO kanban_columns (name, position) VALUES (?, ?)", (name, position))
    conn.commit()
    conn.close()

def get_all_columns():
    """Retrieves all Kanban columns, ordered by position."""
    conn = get_db_connection()
    columns = conn.execute("SELECT * FROM kanban_columns ORDER BY position").fetchall()
    conn.close()
    return columns

def create_card(column_id, title, description=None, assignee=None, due_date=None, created_at=None):
    """Adds a new card to a specified Kanban column."""
    conn = get_db_connection()
    cursor = conn.cursor()
    due_date_utc_str = time_utils.to_utc(due_date).isoformat() if isinstance(due_date, datetime.datetime) else due_date
    created_at_utc_str = time_utils.to_utc(created_at).isoformat() if isinstance(created_at, datetime.datetime) else time_utils.to_utc(datetime.datetime.now()).isoformat()
    cursor.execute("INSERT INTO kanban_cards (column_id, title, description, assignee, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?)", (column_id, title, description, assignee, due_date_utc_str, created_at_utc_str))
    conn.commit()
    card_id = cursor.lastrowid
    conn.close()
    return card_id

def get_cards_by_column(column_id):
    """Retrieves all cards for a given Kanban column."""
    conn = get_db_connection()
    cards = conn.execute("SELECT id, column_id, title, description, created_at, started_at, finished_at, assignee, due_date FROM kanban_cards WHERE column_id = ? ORDER BY created_at", (column_id,)).fetchall()
    conn.close()
    return cards

def move_card(card_id, new_column_id):
    """Moves a card to a new Kanban column and updates timestamps."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the name of the new column
    cursor.execute("SELECT name FROM kanban_columns WHERE id = ?", (new_column_id,))
    column_name = cursor.fetchone()['name']

    current_utc_time = time_utils.to_utc(datetime.datetime.now()).isoformat()

    # Update timestamps based on the column name
    if column_name == "En Progreso":
        cursor.execute("UPDATE kanban_cards SET column_id = ?, started_at = ? WHERE id = ?", (new_column_id, current_utc_time, card_id))
    elif column_name == "Realizadas":
        cursor.execute("UPDATE kanban_cards SET column_id = ?, finished_at = ? WHERE id = ?", (new_column_id, current_utc_time, card_id))
    else:
        cursor.execute("UPDATE kanban_cards SET column_id = ? WHERE id = ?", (new_column_id, card_id))
    
    conn.commit()
    conn.close()

def delete_card(card_id):
    """Deletes a card from the database."""
    conn = get_db_connection()
    conn.execute("DELETE FROM kanban_cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()

def update_card(card_id, new_title, new_description=None, new_assignee=None, new_due_date=None):
    """Updates the title, description, assignee, and due date of an existing Kanban card."""
    conn = get_db_connection()
    new_due_date_utc_str = time_utils.to_utc(new_due_date).isoformat() if isinstance(new_due_date, datetime.datetime) else new_due_date
    conn.execute("UPDATE kanban_cards SET title = ?, description = ?, assignee = ?, due_date = ? WHERE id = ?", (new_title, new_description, new_assignee, new_due_date_utc_str, card_id))
    conn.commit()
    conn.close()



def generate_kanban_report():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT kc.id, kc.title, kc.description, kco.name as column_name, kc.due_date, kc.assignee, kc.created_at, kc.started_at, kc.finished_at FROM kanban_cards kc JOIN kanban_columns kco ON kc.column_id = kco.id")
    cards_data = cursor.fetchall()
    report = []
    for card in cards_data:
        report.append({
            "id": card[0],
            "title": card[1],
            "description": card[2],
            "column_name": card[3],
            "due_date": card[4],
            "assigned_to": card[5],
            "created_at": card[6],
            "started_at": card[7],
            "finished_at": card[8]
        })
    conn.close()
    return report


def get_all_cards():
    """Retrieves all Kanban cards from the database."""
    conn = get_db_connection()
    cards = conn.execute("SELECT id, column_id, title, description, created_at, started_at, finished_at, due_date FROM kanban_cards ORDER BY id DESC").fetchall()
    conn.close()
    return cards

def get_cards_due_between(start_date, end_date):
    """Retrieves cards with a due date between the given dates."""
    conn = get_db_connection()
    cards = conn.execute("SELECT title, due_date, assignee FROM kanban_cards WHERE due_date BETWEEN ? AND ?", (start_date, end_date)).fetchall()
    conn.close()
    return cards

