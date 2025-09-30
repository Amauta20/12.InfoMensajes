from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDateTimeEdit, QDialogButtonBox
from PyQt5.QtCore import QDateTime, Qt

class AddReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Recordatorio")
        self.layout = QVBoxLayout(self)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Texto del recordatorio")
        self.layout.addWidget(self.text_input)

        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setDateTime(QDateTime.currentDateTime())
        self.datetime_input.setCalendarPopup(True)
        self.layout.addWidget(self.datetime_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        return self.text_input.text(), self.datetime_input.dateTime()
