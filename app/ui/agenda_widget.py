from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QListWidgetItem, QCheckBox, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from app.db.reminders_manager import RemindersManager
from app.db.settings_manager import SettingsManager
from app.db import settings_manager, database
from app.utils import time_utils
from app.ui.add_reminder_dialog import AddReminderDialog
from app.ui.edit_reminder_dialog import EditReminderDialog

class AgendaWidget(QWidget):
    agenda_updated = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.manager = RemindersManager(self.conn)
        self.settings_manager = SettingsManager.get_instance()
        self.layout = QVBoxLayout(self)

        self.add_reminder_button = QPushButton("Nuevo Recordatorio")
        self.add_reminder_button.clicked.connect(self.add_reminder)
        self.layout.addWidget(self.add_reminder_button)

        self.agenda_list = QListWidget()
        self.layout.addWidget(self.agenda_list)

        self.load_agenda_items()

    def load_agenda_items(self):
        self.agenda_list.clear()
        all_due_items = self.manager.get_all_due_items()
        for item_data in all_due_items:
            item_widget = self.create_agenda_item_widget(item_data)
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.agenda_list.addItem(list_item)
            self.agenda_list.setItemWidget(list_item, item_widget)

    def create_agenda_item_widget(self, item_data):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        checkbox = QCheckBox()
        checkbox.setChecked(item_data['is_completed'])
        if item_data['type'] == 'Recordatorio':
            checkbox.stateChanged.connect(lambda state, source_id=item_data['source_id']: self.toggle_reminder_completed(source_id, state))
        else:
            checkbox.setEnabled(False)

        layout.addWidget(checkbox)

        due_at_str = item_data['due_at']
        formatted_due_at = ""
        if due_at_str:
            try:
                utc_dt = QDateTime.fromString(due_at_str, Qt.DateFormat.ISODate)
                if not utc_dt.isValid():
                    utc_dt = QDateTime.fromString(due_at_str, "yyyy-MM-ddTHH:mm:ss.zzzZ")
                
                if utc_dt.isValid():
                    local_dt = utc_dt.toLocalTime()
                    formatted_due_at = local_dt.toString(time_utils.convert_strftime_to_qt_format(self.settings_manager.get_datetime_format()))
            except Exception as e:
                print(f"Error parsing due_at in AgendaWidget: {due_at_str}, Error: {e}")

        text = f"[{item_data['type']}] {item_data['text']} - {formatted_due_at}"
        label = QLabel(text)
        layout.addWidget(label)

        layout.addStretch()

        if item_data['type'] == 'Recordatorio':
            edit_button = QPushButton("✏️")
            edit_button.setFixedWidth(30)
            edit_button.clicked.connect(lambda checked, reminder_id=item_data['source_id']: self.edit_reminder(reminder_id))
            layout.addWidget(edit_button)

            delete_button = QPushButton("🗑")
            delete_button.setFixedWidth(30)
            delete_button.clicked.connect(lambda checked, reminder_id=item_data['source_id']: self.delete_reminder(reminder_id))
            layout.addWidget(delete_button)

        widget.adjustSize()
        return widget

    def edit_reminder(self, reminder_id):
        reminder = self.manager.get_reminder(reminder_id)
        if reminder:
            current_text = reminder['text']
            current_due_at = QDateTime.fromString(reminder['due_at'], Qt.DateFormat.ISODate)
            dialog = EditReminderDialog(current_text, current_due_at, self)
            if dialog.exec():
                new_text, new_due_at = dialog.getReminderData()
                new_due_at_iso = time_utils.qdatetime_to_utc_iso(new_due_at)
                self.manager.update_reminder(reminder_id, text=new_text, due_at=new_due_at_iso)
                self.load_agenda_items()
                self.agenda_updated.emit()

    def add_reminder(self):
        dialog = AddReminderDialog(self)
        if dialog.exec():
            text, due_at = dialog.getReminderData()
            due_at_iso = time_utils.qdatetime_to_utc_iso(due_at)
            self.manager.create_reminder(text, due_at_iso)
            self.load_agenda_items()
            self.agenda_updated.emit()

    def delete_reminder(self, reminder_id):
        reply = QMessageBox.question(self, 'Confirmar Eliminación', 
                                     '¿Estás seguro de que quieres eliminar este recordatorio?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_reminder(reminder_id)
            self.load_agenda_items()
            self.agenda_updated.emit()

    def toggle_reminder_completed(self, reminder_id, state):
        is_completed = 1 if state == Qt.CheckState.Checked.value else 0
        self.manager.update_reminder(reminder_id, is_completed=is_completed)
        self.load_agenda_items()
        self.agenda_updated.emit()
