from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt

class EditNoteDialog(QDialog):
    def __init__(self, initial_content="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Nota")
        self.setModal(True)
        self.setFixedSize(400, 300)

        self.layout = QVBoxLayout(self)

        self.note_editor = QTextEdit()
        self.note_editor.setPlainText(initial_content)
        self.layout.addWidget(self.note_editor)

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

    def get_new_content(self):
        return self.note_editor.toPlainText().strip()
