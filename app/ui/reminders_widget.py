from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QListWidgetItem, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from app.db import reminders_manager
from app.ui.add_reminder_dialog import AddReminderDialog

class RemindersWidget(QWidget):
    reminders_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.add_button = QPushButton("Nuevo Recordatorio")
        self.add_button.clicked.connect(self.add_reminder)
        self.layout.addWidget(self.add_button)

        self.reminders_list = QListWidget()
        self.layout.addWidget(self.reminders_list)

        self.load_reminders()

    def load_reminders(self):
        self.reminders_list.clear()
        reminders = reminders_manager.get_all_reminders()
        for reminder in reminders:
            item_widget = self.create_reminder_item_widget(reminder)
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.reminders_list.addItem(list_item)
            self.reminders_list.setItemWidget(list_item, item_widget)

    def create_reminder_item_widget(self, reminder):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        checkbox = QCheckBox()
        checkbox.setChecked(reminder['is_completed'])
        checkbox.stateChanged.connect(lambda state, reminder_id=reminder['id']: self.toggle_reminder_completed(reminder_id, state))
        layout.addWidget(checkbox)

        due_at_str = reminder['due_at']
        if due_at_str:
            utc_dt = QDateTime.fromString(due_at_str, Qt.ISODate)
            local_dt = utc_dt.toLocalTime()
            formatted_due_at = local_dt.toString("dd/MM/yyyy HH:mm")
        else:
            formatted_due_at = ""

        text = f"{reminder['text']} - {formatted_due_at}"
        label = QPushButton(text) # Using QPushButton to make it clickable for editing
        label.setStyleSheet("border: none; text-align: left;")
        # label.clicked.connect(lambda checked, reminder_id=reminder['id']: self.edit_reminder(reminder_id))
        layout.addWidget(label)

        delete_button = QPushButton("Eliminar")
        delete_button.clicked.connect(lambda checked, reminder_id=reminder['id']: self.delete_reminder(reminder_id))
        layout.addWidget(delete_button)

        return widget

    def add_reminder(self):
        dialog = AddReminderDialog(self)
        if dialog.exec():
            text, qdt = dialog.get_data()
            if text:
                utc_dt_str = qdt.toUTC().toString(Qt.ISODate)
                reminders_manager.create_reminder(text, utc_dt_str)
                self.load_reminders()
                self.reminders_updated.emit()

    def delete_reminder(self, reminder_id):
        reminders_manager.delete_reminder(reminder_id)
        self.load_reminders()
        self.reminders_updated.emit()

    def toggle_reminder_completed(self, reminder_id, state):
        is_completed = 1 if state == Qt.Checked else 0
        reminders_manager.update_reminder(reminder_id, is_completed=is_completed)
        self.reminders_updated.emit()
