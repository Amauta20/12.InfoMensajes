from PyQt6.QtWidgets import QFormLayout, QLineEdit, QDateEdit, QTimeEdit, QHBoxLayout, QMessageBox
from PyQt6.QtCore import QDateTime
from app.utils import time_utils
from app.ui.base_dialog import BaseDialog

class AddReminderDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__("Nuevo Recordatorio", parent)

        form_layout = QFormLayout()
        self.reminder_text_input = QLineEdit()
        form_layout.addRow("Texto del recordatorio:", self.reminder_text_input)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDateTime(time_utils.get_current_qdatetime())
        self.due_time_edit = QTimeEdit()
        self.due_time_edit.setDateTime(time_utils.get_current_qdatetime())

        due_layout = QHBoxLayout()
        due_layout.addWidget(self.due_date_edit)
        due_layout.addWidget(self.due_time_edit)
        form_layout.addRow("Fecha y Hora de Vencimiento:", due_layout)

        self.add_content(form_layout)
        self.reminder_text_input.setFocus()

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
