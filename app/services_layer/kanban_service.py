from app.db.kanban_manager import KanbanManager
import datetime

class KanbanService:
    """
    A service layer for handling business logic related to the Kanban board.
    It decouples the UI from the data access layer.
    """
    def __init__(self, kanban_manager: KanbanManager):
        self.kanban_manager = kanban_manager

    def create_default_columns(self):
        """Ensures the default Kanban columns exist."""
        self.kanban_manager.create_default_columns()

    def get_all_columns(self):
        """Retrieves all Kanban columns."""
        return self.kanban_manager.get_all_columns()

    def create_card(self, column_id, title, description=None, assignee=None, due_date=None, created_at=None, started_at=None, finished_at=None, start_date=None, end_date=None):
        """Adds a new card to a specified Kanban column."""
        return self.kanban_manager.create_card(column_id, title, description, assignee, due_date, created_at, started_at, finished_at, start_date, end_date)

    def get_cards_by_column(self, column_id):
        """Retrieves all cards for a given Kanban column."""
        return self.kanban_manager.get_cards_by_column(column_id)

    def move_card(self, card_id, new_column_id):
        """Moves a card to a new Kanban column."""
        self.kanban_manager.move_card(card_id, new_column_id)

    def delete_card(self, card_id):
        """Deletes a card."""
        self.kanban_manager.delete_card(card_id)

    def update_card(self, card_id, new_title, new_description=None, new_assignee=None, new_due_date=None, new_start_date=None, new_end_date=None):
        """Updates an existing Kanban card."""
        self.kanban_manager.update_card(card_id, new_title, new_description, new_assignee, new_due_date, new_start_date, new_end_date)

    def get_card_details(self, card_id):
        """Retrieves details for a specific Kanban card."""
        return self.kanban_manager.get_card_details(card_id)

    def generate_kanban_report(self):
        """Generates a report of all Kanban cards."""
        return self.kanban_manager.generate_kanban_report()

    def get_all_cards(self):
        """Retrieves all Kanban cards."""
        return self.kanban_manager.get_all_cards()

    def get_cards_due_between(self, start_date, end_date):
        """Retrieves cards with a due date between the given dates."""
        return self.kanban_manager.get_cards_due_between(start_date, end_date)

    def get_all_kanban_cards_for_gantt(self):
        """Retrieves all Kanban cards for Gantt chart processing."""
        return self.kanban_manager.get_all_kanban_cards_for_gantt()
