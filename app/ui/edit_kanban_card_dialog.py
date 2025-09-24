from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel
from PySide6.QtCore import Qt

class EditKanbanCardDialog(QDialog):
    def __init__(self, initial_title="", initial_description="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Kanban Card")
        self.setModal(True)
        self.setFixedSize(400, 350)

        self.layout = QVBoxLayout(self)

        # Title input
        self.title_label = QLabel("Title:")
        self.title_input = QLineEdit()
        self.title_input.setText(initial_title)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.title_input)

        # Description input
        self.description_label = QLabel("Description:")
        self.description_editor = QTextEdit()
        self.description_editor.setPlainText(initial_description)
        self.layout.addWidget(self.description_label)
        self.layout.addWidget(self.description_editor)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addStretch()

        self.layout.addLayout(self.button_layout)

    def get_new_data(self):
        new_title = self.title_input.text().strip()
        new_description = self.description_editor.toPlainText().strip()
        return new_title, new_description
