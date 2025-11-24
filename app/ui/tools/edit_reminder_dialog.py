from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QTimeEdit, QHBoxLayout, QDialogButtonBox, QMessageBox
from PyQt6.QtCore import QDateTime
from app.utils import time_utils

class EditReminderDialog(QDialog):
    def __init__(self, current_text, current_due_date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Recordatorio")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.reminder_text_input = QLineEdit(current_text)
        self.form_layout.addRow("Texto del recordatorio:", self.reminder_text_input)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_time_edit = QTimeEdit()

        if current_due_date:
            self.due_date_edit.setDate(current_due_date.date())
            self.due_time_edit.setTime(current_due_date.time())

        due_layout = QHBoxLayout()
        due_layout.addWidget(self.due_date_edit)
        due_layout.addWidget(self.due_time_edit)
        self.form_layout.addRow("Fecha y Hora de Vencimiento:", due_layout)

        self.layout.addLayout(self.form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def validate_and_accept(self):
        text = self.reminder_text_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Error de Entrada", "El texto del recordatorio no puede estar vacío.")
            return
        self.accept()

    def getReminderData(self):
        text = self.reminder_text_input.text().strip()
        date = self.due_date_edit.date()
        time = self.due_time_edit.time()
        due_at = QDateTime(date, time)
        return text, due_at
