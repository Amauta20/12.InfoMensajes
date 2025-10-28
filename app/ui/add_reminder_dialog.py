from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDateTimeEdit, QDialogButtonBox, QDateEdit, QTimeEdit, QHBoxLayout
from PyQt6.QtCore import QDateTime, Qt
from app.utils import time_utils
from app.db.settings_manager import SettingsManager

class AddReminderDialog(QDialog):
    def __init__(self, settings_manager_instance, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager_instance
        self.setWindowTitle("Nuevo Recordatorio")
        self.layout = QVBoxLayout(self)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Texto del recordatorio")
        self.layout.addWidget(self.text_input)

        datetime_layout = QHBoxLayout()
        self.date_input = QDateEdit()
        self.date_input.setDateTime(time_utils.get_current_qdatetime())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(self.settings_manager.get_date_format()))
        datetime_layout.addWidget(self.date_input)

        self.time_input = QTimeEdit()
        self.time_input.setDateTime(time_utils.get_current_qdatetime())
        self.time_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(self.settings_manager.get_time_format()))
        datetime_layout.addWidget(self.time_input)
        self.layout.addLayout(datetime_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        return self.text_input.text(), QDateTime(self.date_input.date(), self.time_input.time())
