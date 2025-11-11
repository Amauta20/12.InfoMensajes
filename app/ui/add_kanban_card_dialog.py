from PyQt6.QtWidgets import QVBoxLayout, QLineEdit, QTextEdit, QLabel, QMessageBox, QDateEdit, QTimeEdit, QHBoxLayout
from PyQt6.QtCore import QDateTime
from app.utils import time_utils
from app.db.settings_manager import SettingsManager
from app.ui.base_dialog import BaseDialog

class AddKanbanCardDialog(BaseDialog):
    def __init__(self, settings_manager_instance, parent=None):
        super().__init__("Añadir Tarjeta Kanban", parent)
        self.settings_manager = settings_manager_instance
        self.setFixedSize(400, 450)

        content_layout = QVBoxLayout()

        # Title input
        self.title_label = QLabel("Título:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título de la tarea")
        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.title_input)

        # Description input
        self.description_label = QLabel("Descripción:")
        self.description_editor = QTextEdit()
        self.description_editor.setPlaceholderText("Descripción detallada de la tarea (opcional)")
        content_layout.addWidget(self.description_label)
        content_layout.addWidget(self.description_editor)

        # Assignee input
        self.assignee_label = QLabel("Encargado:")
        self.assignee_input = QLineEdit()
        self.assignee_input.setPlaceholderText("Nombre del encargado (opcional)")
        content_layout.addWidget(self.assignee_label)
        content_layout.addWidget(self.assignee_input)

        # Due Date input
        self.due_date_label = QLabel("Fecha de Entrega:")
        content_layout.addWidget(self.due_date_label)

        datetime_layout = QHBoxLayout()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(self.settings_manager.get_date_format()))
        self.date_input.setDateTime(time_utils.get_current_qdatetime())
        datetime_layout.addWidget(self.date_input)

        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(self.settings_manager.get_time_format()))
        self.time_input.setDateTime(time_utils.get_current_qdatetime())
        datetime_layout.addWidget(self.time_input)
        content_layout.addLayout(datetime_layout)

        self.add_content(content_layout)
        self.title_input.setFocus()

    def validate_and_accept(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Error de Entrada", "El título de la tarea no puede estar vacío.")
            return
        
        self.accept()

    def get_card_data(self):
        title = self.title_input.text().strip()
        description = self.description_editor.toPlainText().strip()
        assignee = self.assignee_input.text().strip()
        due_date = QDateTime(self.date_input.date(), self.time_input.time())
        return title, description, assignee, due_date
