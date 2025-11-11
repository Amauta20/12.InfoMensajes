import datetime
from app.db.reminders_manager import RemindersManager
from app.services_layer.kanban_service import KanbanService
from app.services_layer.checklist_service import ChecklistService

class RemindersService:
    """
    A service layer for handling business logic related to reminders and agenda items.
    It decouples the UI from the data access layer and aggregates data from multiple sources.
    """
    def __init__(self, reminders_manager: RemindersManager, kanban_service: KanbanService, checklist_service: ChecklistService):
        self.reminders_manager = reminders_manager
        self.kanban_service = kanban_service
        self.checklist_service = checklist_service

    def get_all_due_items(self):
        """Retrieves all items with a due date from reminders, Kanban cards, and checklist items."""
        all_items = []

        # 1. Get Reminders
        reminders = self.get_all_reminders()
        for reminder in reminders:
            if reminder['due_at']:
                all_items.append({
                    'type': 'Recordatorio',
                    'text': reminder['text'],
                    'due_at': reminder['due_at'],
                    'source_id': reminder['id'],
                    'is_completed': reminder['is_completed']
                })

        # 2. Get Kanban Cards
        kanban_cards = self.kanban_service.get_all_cards()
        for card in kanban_cards:
            if card['due_date']:
                all_items.append({
                    'type': 'Kanban',
                    'text': card['title'],
                    'due_at': card['due_date'],
                    'source_id': card['id'],
                    'is_completed': card['column_name'] == 'Done'
                })

        # 3. Get Checklist Items
        checklists = self.checklist_service.get_all_checklists()
        for checklist in checklists:
            for item in checklist.get('items', []):
                if item['due_at']:
                    all_items.append({
                        'type': 'Checklist',
                        'text': item['text'],
                        'due_at': item['due_at'],
                        'source_id': item['id'],
                        'is_completed': item['is_checked']
                    })
        
        all_items.sort(key=lambda x: x['due_at'])
        
        return all_items

    def create_reminder(self, text, due_at):
        """Creates a new reminder."""
        return self.reminders_manager.create_reminder(text, due_at)

    def get_all_reminders(self):
        """Retrieves all reminders."""
        return self.reminders_manager.get_all_reminders()

    def get_reminder(self, reminder_id):
        """Retrieves a single reminder by its ID."""
        return self.reminders_manager.get_reminder(reminder_id)

    def get_actual_due_reminders(self):
        """Retrieves all due and not notified reminders."""
        return self.reminders_manager.get_actual_due_reminders()

    def get_pre_due_reminders(self, pre_notification_offsets_minutes):
        """Retrieves reminders that are due within the pre-notification offsets."""
        return self.reminders_manager.get_pre_due_reminders(pre_notification_offsets_minutes)

    def update_reminder(self, reminder_id, text=None, due_at=None, is_completed=None, is_notified=None, pre_notified_at=None):
        """Updates a reminder."""
        self.reminders_manager.update_reminder(reminder_id, text, due_at, is_completed, is_notified, pre_notified_at)

    def delete_reminder(self, reminder_id):
        """Deletes a reminder."""
        self.reminders_manager.delete_reminder(reminder_id)

    def get_reminders_due_between(self, start_date, end_date):
        """Retrieves reminders with a due date between the given dates."""
        return self.reminders_manager.get_reminders_due_between(start_date, end_date)

    def get_agenda_item_for_reminder(self, reminder_id):
        """Retrieves a single reminder and formats it as an agenda item."""
        reminder = self.get_reminder(reminder_id)
        if reminder and reminder['due_at']:
            return {
                'type': 'Recordatorio',
                'text': reminder['text'],
                'due_at': reminder['due_at'],
                'source_id': reminder['id'],
                'is_completed': reminder['is_completed']
            }
        return None
