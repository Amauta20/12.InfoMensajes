from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

class WelcomeWidget(QWidget):
    add_service_requested = Signal() # Signal to request opening the AddServiceDialog

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(20)

        self.welcome_label = QLabel("¡Bienvenido a InfoMensajero!")
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.welcome_label)

        self.instructions_label = QLabel("Para empezar, añade tu primer servicio de mensajería o productividad.")
        self.instructions_label.setStyleSheet("font-size: 14px;")
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.instructions_label)

        self.add_button = QPushButton("Añadir Tu Primer Servicio")
        self.add_button.setFixedSize(200, 40)
        self.add_button.clicked.connect(self.add_service_requested.emit)
        self.layout.addWidget(self.add_button)
