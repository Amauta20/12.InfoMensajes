from app.db.checklist_manager import ChecklistManager
import datetime

class ChecklistService:
    """
    A service layer for handling business logic related to checklists.
    It decouples the UI from the data access layer.
    """
    def __init__(self, checklist_manager: ChecklistManager):
        self.checklist_manager = checklist_manager

    def create_checklist(self, name, kanban_card_id=None):
        """Creates a new checklist."""
        return self.checklist_manager.create_checklist(name, kanban_card_id)

    def get_all_checklists(self):
        """Retrieves all checklists with their items."""
        return self.checklist_manager.get_all_checklists()

    def get_checklist(self, checklist_id):
        """Retrieves a single checklist with its items."""
        return self.checklist_manager.get_checklist(checklist_id)

    def update_checklist_name(self, checklist_id, new_name):
        """Updates the name of a checklist."""
        self.checklist_manager.update_checklist_name(checklist_id, new_name)

    def delete_checklist(self, checklist_id):
        """Deletes a checklist and all its items."""
        self.checklist_manager.delete_checklist(checklist_id)

    def add_item_to_checklist(self, checklist_id, text, due_at=None):
        """Adds a new item to a checklist."""
        return self.checklist_manager.add_item_to_checklist(checklist_id, text, due_at)

    def update_checklist_item(self, item_id, text=None, is_checked=None, due_at=None, is_notified=None, pre_notified_at=None):
        """Updates a checklist item."""
        self.checklist_manager.update_checklist_item(item_id, text, is_checked, due_at, is_notified, pre_notified_at)

    def delete_checklist_item(self, item_id):
        """Deletes a checklist item."""
        self.checklist_manager.delete_checklist_item(item_id)

    def get_checklist_item(self, item_id):
        """Retrieves a single checklist item."""
        return self.checklist_manager.get_checklist_item(item_id)

    def get_checklists_for_card(self, kanban_card_id):
        """Retrieves all checklists for a given Kanban card."""
        return self.checklist_manager.get_checklists_for_card(kanban_card_id)

    def get_independent_checklists(self):
        """Retrieves all checklists not associated with a Kanban card."""
        return self.checklist_manager.get_independent_checklists()

    def get_items_due_between(self, start_date, end_date):
        """Retrieves all checklist items due between two dates."""
        return self.checklist_manager.get_items_due_between(start_date, end_date)

    def get_pre_due_checklist_items(self, pre_notification_offsets_minutes):
        """Retrieves checklist items that are due within the pre-notification offsets."""
        return self.checklist_manager.get_pre_due_checklist_items(pre_notification_offsets_minutes)

    def get_actual_due_checklist_items(self):
        """Retrieves all due and not notified checklist items."""
        return self.checklist_manager.get_actual_due_checklist_items()
