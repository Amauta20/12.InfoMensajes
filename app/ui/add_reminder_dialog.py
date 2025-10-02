from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDateTimeEdit, QDialogButtonBox
from PyQt6.QtCore import QDateTime, Qt
from app.utils import time_utils
from app.db import settings_manager

class AddReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Recordatorio")
        self.layout = QVBoxLayout(self)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Texto del recordatorio")
        self.layout.addWidget(self.text_input)

        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setDateTime(time_utils.get_current_qdatetime())
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(settings_manager.get_datetime_format()))
        self.layout.addWidget(self.datetime_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        return self.text_input.text(), self.datetime_input.dateTime()
