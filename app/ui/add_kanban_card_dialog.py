from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt

class AddKanbanCardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Tarjeta Kanban")
        self.setModal(True)
        self.setFixedSize(400, 450)

        self.layout = QVBoxLayout(self)

        # Title input
        self.title_label = QLabel("Título:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título de la tarea")
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.title_input)

        # Description input
        self.description_label = QLabel("Descripción:")
        self.description_editor = QTextEdit()
        self.description_editor.setPlaceholderText("Descripción detallada de la tarea (opcional)")
        self.layout.addWidget(self.description_label)
        self.layout.addWidget(self.description_editor)

        # Assignee input
        self.assignee_label = QLabel("Encargado:")
        self.assignee_input = QLineEdit()
        self.assignee_input.setPlaceholderText("Nombre del encargado (opcional)")
        self.layout.addWidget(self.assignee_label)
        self.layout.addWidget(self.assignee_input)

        # Due Date input
        self.due_date_label = QLabel("Fecha de Entrega (YYYY-MM-DD HH:MM:SS):")
        self.due_date_input = QLineEdit()
        self.due_date_input.setPlaceholderText("Opcional (ej. 2025-12-31 23:59:59)")
        self.layout.addWidget(self.due_date_label)
        self.layout.addWidget(self.due_date_input)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Añadir")
        self.add_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addStretch()

        self.layout.addLayout(self.button_layout)

    def validate_and_accept(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Error de Entrada", "El título de la tarea no puede estar vacío.")
            return
        
        # Basic due date validation (optional, can be enhanced)
        due_date_str = self.due_date_input.text().strip()
        if due_date_str:
            try:
                # Attempt to parse the date to ensure it's in a valid format
                # This is a basic check, more robust validation might be needed
                from datetime import datetime
                datetime.strptime(due_date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "El formato de la fecha de entrega debe ser YYYY-MM-DD HH:MM:SS.")
                return

        self.accept()

    def get_card_data(self):
        title = self.title_input.text().strip()
        description = self.description_editor.toPlainText().strip()
        assignee = self.assignee_input.text().strip()
        due_date = self.due_date_input.text().strip()
        return title, description, assignee, due_date
