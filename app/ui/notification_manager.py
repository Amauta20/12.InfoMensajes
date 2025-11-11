import os
from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QSystemTrayIcon

# Need to import time_utils for check_for_notifications
from app.utils import time_utils

class NotificationManager(QObject):
    """Manages system tray icon and periodic notifications for reminders and checklists."""
    def __init__(self, parent, settings_manager, reminders_service, checklist_service):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.reminders_service = reminders_service
        self.checklist_service = checklist_service

        self._setup_tray_icon()
        self._setup_notification_timer()

    def _setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self.parent())
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icon.ico'))
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.show()

    def _setup_notification_timer(self):
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_for_notifications)
        self.notification_timer.start(10000) # Check every 10 seconds

    def show_notification(self, title, message):
        """Displays a system tray notification."""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)

    def check_for_notifications(self):
        """
        Checks for pre-due and due reminders and checklist items,
        and displays system tray notifications.
        """
        pre_notification_offsets_minutes = self.settings_manager.get_pre_notification_offset()

        # Check for pre-due reminders
        for reminder in self.reminders_service.get_pre_due_reminders(pre_notification_offsets_minutes):
            self.show_notification("Recordatorio Próximo", f"'{reminder['text']}' vence pronto ({reminder['due_at']})")
            self.reminders_service.update_reminder(reminder['id'], pre_notified_at=time_utils.to_utc(time_utils.datetime_from_qdatetime(time_utils.get_current_qdatetime())).isoformat())

        # Check for pre-due checklist items
        for item in self.checklist_service.get_pre_due_checklist_items(pre_notification_offsets_minutes):
            self.show_notification("Tarea de Checklist Próxima", f"'{item['text']}' vence pronto ({item['due_at']})")
            self.checklist_service.update_checklist_item(item['id'], pre_notified_at=time_utils.to_utc(time_utils.datetime_from_qdatetime(time_utils.get_current_qdatetime())).isoformat())

        # Check for due reminders
        for reminder in self.reminders_service.get_actual_due_reminders():
            self.show_notification("Recordatorio", reminder['text'])
            self.reminders_service.update_reminder(reminder['id'], is_notified=1)

        # Check for due checklist items
        for item in self.checklist_service.get_actual_due_checklist_items():
            self.show_notification("Tarea de Checklist", item['text'])
            self.checklist_service.update_checklist_item(item['id'], is_notified=1)

    def show_pomodoro_notification(self, mode):
        """Displays a notification for Pomodoro timer events."""
        if mode == "Pomodoro":
            title = "¡Tiempo de descanso!"
            message = "¡Buen trabajo! Tomate un descanso corto."
        else:
            title = "¡De vuelta al trabajo!"
            message = "El descanso ha terminado. ¡A concentrarse!"
        self.show_notification(title, message)
