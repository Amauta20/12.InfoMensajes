from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel, QDateEdit, QTimeEdit
from PyQt6.QtCore import Qt, QDateTime
from app.utils import time_utils
from app.db.settings_manager import SettingsManager

class EditKanbanCardDialog(QDialog):
    def __init__(self, settings_manager_instance, initial_title="", initial_description="", initial_assignee="", initial_due_date="", parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager_instance
        self.setWindowTitle("Editar Tarjeta Kanban")
        self.setModal(True)
        self.setFixedSize(400, 450)

        self.layout = QVBoxLayout(self)

        # Title input
        self.title_label = QLabel("Título:")
        self.title_input = QLineEdit()
        self.title_input.setText(initial_title)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.title_input)

        # Description input
        self.description_label = QLabel("Descripción:")
        self.description_editor = QTextEdit()
        self.description_editor.setPlainText(initial_description)
        self.layout.addWidget(self.description_label)
        self.layout.addWidget(self.description_editor)

        # Assignee input
        self.assignee_label = QLabel("Encargado:")
        self.assignee_input = QLineEdit()
        self.assignee_input.setText(initial_assignee)
        self.layout.addWidget(self.assignee_label)
        self.layout.addWidget(self.assignee_input)

        # Due Date input
        self.due_date_label = QLabel("Fecha de Entrega:")
        self.layout.addWidget(self.due_date_label)

        datetime_layout = QHBoxLayout()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(self.settings_manager.get_date_format()))
        datetime_layout.addWidget(self.date_input)

        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(self.settings_manager.get_time_format()))
        datetime_layout.addWidget(self.time_input)
        self.layout.addLayout(datetime_layout)

        if initial_due_date:
            dt = QDateTime.fromString(initial_due_date, Qt.DateFormat.ISODate)
            self.date_input.setDateTime(dt)
            self.time_input.setDateTime(dt)
        else:
            current_dt = time_utils.get_current_qdatetime()
            self.date_input.setDateTime(current_dt)
            self.time_input.setDateTime(current_dt)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addStretch()

        self.layout.addLayout(self.button_layout)

    def get_new_data(self):
        new_title = self.title_input.text().strip()
        new_description = self.description_editor.toPlainText().strip()
        new_assignee = self.assignee_input.text().strip()
        new_due_date = QDateTime(self.date_input.date(), self.time_input.time())
        return new_title, new_description, new_assignee, new_due_date
