from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QListWidgetItem, QCheckBox, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from app.services_layer.reminders_service import RemindersService
from app.db.settings_manager import SettingsManager
from app.utils import time_utils
from app.ui.tools.add_reminder_dialog import AddReminderDialog
from app.ui.tools.edit_reminder_dialog import EditReminderDialog

class AgendaWidget(QWidget):
    agenda_updated = pyqtSignal()

    def __init__(self, reminders_service: RemindersService, parent=None):
        super().__init__(parent)
        self.reminders_service = reminders_service
        self.settings_manager = SettingsManager.get_instance()
        self.layout = QVBoxLayout(self)

        self.add_reminder_button = QPushButton("Nuevo Recordatorio")
        self.add_reminder_button.clicked.connect(self.add_reminder)
        self.layout.addWidget(self.add_reminder_button)

        self.agenda_list = QListWidget()
        self.layout.addWidget(self.agenda_list)

        self.load_agenda_items()

    def load_agenda_items(self):
        """Clears and reloads all items. Used for initial load."""
        self.agenda_list.clear()
        all_due_items = self.reminders_service.get_all_due_items()
        for item_data in all_due_items:
            self._add_item_to_list_widget(item_data)

    def _add_item_to_list_widget(self, item_data, row=None):
        """Creates and adds a single item widget to the list."""
        item_widget = self._create_agenda_item_widget(item_data)
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        
        # Store ID and type for later retrieval
        list_item.setData(Qt.ItemDataRole.UserRole, {'id': item_data['source_id'], 'type': item_data['type']})

        if row is not None:
            self.agenda_list.insertItem(row, list_item)
        else:
            self.agenda_list.addItem(list_item)
            
        self.agenda_list.setItemWidget(list_item, item_widget)
        return list_item

    def _find_list_item(self, source_id):
        """Finds a QListWidgetItem by its source_id."""
        for i in range(self.agenda_list.count()):
            item = self.agenda_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data.get('id') == source_id:
                return item
        return None

    def _create_agenda_item_widget(self, item_data):
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
            edit_button = QPushButton("\uf044") # Font Awesome edit icon
            edit_button.setStyleSheet("QPushButton { font-family: \"Font Awesome 6 Free\"; font-size: 12px; padding: 0px; margin: 0px; border: none; }")
            edit_button.setFixedSize(24, 24)
            edit_button.clicked.connect(lambda checked, reminder_id=item_data['source_id']: self.edit_reminder(reminder_id))
            layout.addWidget(edit_button)

            delete_button = QPushButton("\uf2ed") # Font Awesome trash icon
            delete_button.setStyleSheet("QPushButton { font-family: \"Font Awesome 6 Free\"; font-size: 12px; padding: 0px; margin: 0px; border: none; }")
            delete_button.setFixedSize(24, 24)
            delete_button.clicked.connect(lambda checked, reminder_id=item_data['source_id']: self.delete_reminder(reminder_id))
            layout.addWidget(delete_button)

        widget.adjustSize()
        return widget

    def edit_reminder(self, reminder_id):
        reminder = self.reminders_service.get_reminder(reminder_id)
        if not reminder:
            return

        current_text = reminder['text']
        current_due_at = QDateTime.fromString(reminder['due_at'], Qt.DateFormat.ISODate)
        dialog = EditReminderDialog(current_text, current_due_at, self)
        
        if dialog.exec():
            new_text, new_due_at = dialog.getReminderData()
            new_due_at_iso = time_utils.qdatetime_to_utc_iso(new_due_at)
            self.reminders_service.update_reminder(reminder_id, text=new_text, due_at=new_due_at_iso)
            
            # Instead of full reload, update the specific item
            list_item = self._find_list_item(reminder_id)
            if list_item:
                row = self.agenda_list.row(list_item)
                self.agenda_list.takeItem(row) # Remove old item
                
                # Re-fetch data to ensure it's fresh
                updated_item_data = self.reminders_service.get_agenda_item_for_reminder(reminder_id)
                if updated_item_data:
                    self._add_item_to_list_widget(updated_item_data, row) # Insert updated item at same position

            self.agenda_updated.emit()

    def add_reminder(self):
        dialog = AddReminderDialog(self)
        if dialog.exec():
            text, due_at = dialog.getReminderData()
            due_at_iso = time_utils.qdatetime_to_utc_iso(due_at)
            new_id = self.reminders_service.create_reminder(text, due_at_iso)
            
            # Instead of full reload, just add the new item
            # This is less efficient as it re-queries, but safer for sorted lists
            self.load_agenda_items() 
            self.agenda_updated.emit()

    def delete_reminder(self, reminder_id):
        reply = QMessageBox.question(self, 'Confirmar Eliminación', 
                                     '¿Estás seguro de que quieres eliminar este recordatorio?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.reminders_service.delete_reminder(reminder_id)
            
            # Instead of full reload, remove the specific item
            list_item = self._find_list_item(reminder_id)
            if list_item:
                row = self.agenda_list.row(list_item)
                self.agenda_list.takeItem(row)
            
            self.agenda_updated.emit()

    def toggle_reminder_completed(self, reminder_id, state):
        is_completed = 1 if state == Qt.CheckState.Checked.value else 0
        self.reminders_service.update_reminder(reminder_id, is_completed=is_completed)
        
        # Find the widget and update its visual state
        list_item = self._find_list_item(reminder_id)
        if list_item:
            widget = self.agenda_list.itemWidget(list_item)
            # The widget is a QWidget containing a layout. Find the QLabel.
            label = widget.findChild(QLabel)
            if label:
                font = label.font()
                font.setStrikeOut(bool(is_completed))
                label.setFont(font)

        self.agenda_updated.emit()