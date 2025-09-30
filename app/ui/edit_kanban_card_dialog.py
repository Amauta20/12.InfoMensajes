from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel, QDateTimeEdit
from PyQt5.QtCore import Qt, QDateTime

class EditKanbanCardDialog(QDialog):
    def __init__(self, initial_title="", initial_description="", initial_assignee="", initial_due_date="", parent=None):
        super().__init__(parent)
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
        self.due_date_input = QDateTimeEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDisplayFormat("dd/MM/yyyy HH:mm")
        if initial_due_date:
            self.due_date_input.setDateTime(QDateTime.fromString(initial_due_date, Qt.ISODate))
        else:
            self.due_date_input.setDateTime(QDateTime.currentDateTime())
        self.layout.addWidget(self.due_date_label)
        self.layout.addWidget(self.due_date_input)

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
        new_due_date = self.due_date_input.dateTime()
        return new_title, new_description, new_assignee, new_due_date
