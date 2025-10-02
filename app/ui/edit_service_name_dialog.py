from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt

class EditServiceNameDialog(QDialog):
    def __init__(self, current_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Nombre del Servicio")
        self.setModal(True)
        self.setFixedSize(300, 120)

        self.layout = QVBoxLayout(self)

        # Name input
        self.name_label = QLabel("Nuevo Nombre del Servicio:")
        self.name_input = QLineEdit()
        self.name_input.setText(current_name)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)

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

    def get_new_name(self):
        return self.name_input.text().strip()
