import datetime
from app.utils import time_utils

class KanbanManager:
    def __init__(self, conn):
        self.conn = conn

    def create_default_columns(self):
        """Ensures the default Kanban columns exist."""
        cursor = self.conn.cursor()
        default_columns = [("Por Hacer", 0), ("En Progreso", 1), ("Realizadas", 2)]
        for name, position in default_columns:
            cursor.execute("INSERT OR IGNORE INTO kanban_columns (name, position) VALUES (?, ?)", (name, position))
        self.conn.commit()

    def get_all_columns(self):
        """Retrieves all Kanban columns, ordered by position."""
        columns = self.conn.execute("SELECT * FROM kanban_columns ORDER BY position").fetchall()
        return columns

    def create_card(self, column_id, title, description=None, assignee=None, due_date=None, created_at=None, started_at=None, finished_at=None, start_date=None, end_date=None):
        """Adds a new card to a specified Kanban column."""
        cursor = self.conn.cursor()
        due_date_utc_str = time_utils.to_utc(due_date).isoformat() if isinstance(due_date, datetime.datetime) else due_date
        created_at_utc_str = time_utils.to_utc(created_at).isoformat() if isinstance(created_at, datetime.datetime) else (created_at if created_at else time_utils.to_utc(datetime.datetime.now()).isoformat())
        started_at_utc_str = time_utils.to_utc(started_at).isoformat() if isinstance(started_at, datetime.datetime) else started_at
        finished_at_utc_str = time_utils.to_utc(finished_at).isoformat() if isinstance(finished_at, datetime.datetime) else finished_at
        start_date_utc_str = time_utils.to_utc(start_date).isoformat() if isinstance(start_date, datetime.datetime) else start_date
        end_date_utc_str = time_utils.to_utc(end_date).isoformat() if isinstance(end_date, datetime.datetime) else end_date
        cursor.execute("INSERT INTO kanban_cards (column_id, title, description, assignee, due_date, created_at, started_at, finished_at, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (column_id, title, description, assignee, due_date_utc_str, created_at_utc_str, started_at_utc_str, finished_at_utc_str, start_date_utc_str, end_date_utc_str))
        self.conn.commit()
        card_id = cursor.lastrowid
        return card_id

    def get_cards_by_column(self, column_id):
        """Retrieves all cards for a given Kanban column."""
        cards = self.conn.execute("SELECT id, column_id, title, description, created_at, started_at, finished_at, assignee, due_date, start_date, end_date FROM kanban_cards WHERE column_id = ? ORDER BY created_at", (column_id,)).fetchall()
        return cards

    def move_card(self, card_id, new_column_id):
        """Moves a card to a new Kanban column and updates timestamps."""
        cursor = self.conn.cursor()

        # Get the name of the new column
        cursor.execute("SELECT name FROM kanban_columns WHERE id = ?", (new_column_id,))
        column_name = cursor.fetchone()['name']

        current_utc_time = time_utils.to_utc(datetime.datetime.now()).isoformat()

        # Get current card details to preserve started_at if moving to 'Realizadas'
        current_card = self.conn.execute("SELECT started_at, finished_at FROM kanban_cards WHERE id = ?", (card_id,)).fetchone()
        current_started_at = current_card['started_at'] if current_card else None

        # Update timestamps based on the column name
        started_at_val = current_started_at
        finished_at_val = None

        if column_name == "Por Hacer":
            started_at_val = None
            finished_at_val = None
        elif column_name == "En Progreso":
            if not current_started_at: # Only set started_at if it's not already set
                started_at_val = current_utc_time
            finished_at_val = None
        elif column_name == "Realizadas":
            if not current_started_at: # If it somehow skipped 'En Progreso'
                started_at_val = current_utc_time
            finished_at_val = current_utc_time

        cursor.execute("UPDATE kanban_cards SET column_id = ?, started_at = ?, finished_at = ? WHERE id = ?", (new_column_id, started_at_val, finished_at_val, card_id))
        
        self.conn.commit()

    def delete_card(self, card_id):
        """Deletes a card from the database."""
        self.conn.execute("DELETE FROM kanban_cards WHERE id = ?", (card_id,))
        self.conn.commit()

    def update_card(self, card_id, new_title, new_description=None, new_assignee=None, new_due_date=None, new_start_date=None, new_end_date=None):
        """Updates the title, description, assignee, due date, start date, and end date of an existing Kanban card."""
        new_due_date_utc_str = time_utils.to_utc(new_due_date).isoformat() if isinstance(new_due_date, datetime.datetime) else new_due_date
        new_start_date_utc_str = time_utils.to_utc(new_start_date).isoformat() if isinstance(new_start_date, datetime.datetime) else new_start_date
        new_end_date_utc_str = time_utils.to_utc(new_end_date).isoformat() if isinstance(new_end_date, datetime.datetime) else new_end_date
        self.conn.execute("UPDATE kanban_cards SET title = ?, description = ?, assignee = ?, due_date = ?, start_date = ?, end_date = ? WHERE id = ?", 
                           (new_title, new_description, new_assignee, new_due_date_utc_str, new_start_date_utc_str, new_end_date_utc_str, card_id))
        self.conn.commit()

    def get_card_details(self, card_id):
        """Retrieves all details for a specific Kanban card."""
        card = self.conn.execute("SELECT id, column_id, title, description, created_at, started_at, finished_at, assignee, due_date, start_date, end_date FROM kanban_cards WHERE id = ?", (card_id,)).fetchone()
        return card

    def generate_kanban_report(self):
        cursor = self.conn.cursor()
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
        return report

    def get_all_cards(self):
        """Retrieves all Kanban cards from the database."""
        cards = self.conn.execute("SELECT id, column_id, title, description, created_at, started_at, finished_at, due_date, start_date, end_date FROM kanban_cards ORDER BY id DESC").fetchall()
        return cards

    def get_cards_due_between(self, start_date, end_date):
        """Retrieves cards with a due date between the given dates."""
        cards = self.conn.execute("SELECT title, due_date, assignee FROM kanban_cards WHERE due_date BETWEEN ? AND ?", (start_date, end_date)).fetchall()
        return cards

    def get_all_kanban_cards_for_gantt(self):
        """Retrieves all Kanban cards for Gantt chart processing."""
        cards = self.conn.execute("SELECT id, column_id, title, description, created_at, started_at, finished_at, due_date FROM kanban_cards").fetchall()
        return cards

