from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QDialogButtonBox
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices

class AboutDialog(QDialog):
    show_help_manual_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de InfoMensajes-Power")
        self.layout = QVBoxLayout(self)

        self.name_label = QLabel("InfoMensajes-Power")
        font = self.name_label.font()
        font.setPointSize(16)
        self.name_label.setFont(font)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name_label)

        self.version_label = QLabel("Versión 1.0.0") # You can make this dynamic
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.version_label)

        self.description_label = QLabel("InfoMensajes-Power es una aplicación para gestionar tus mensajes y recordatorios.")
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.description_label)

        self.website_link = QLabel('<a href="https://github.com/stevecode-b">Visita nuestra página web</a>')
        self.website_link.setOpenExternalLinks(True)
        self.website_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.website_link)

        self.update_button = QPushButton("Buscar Actualizaciones")
        self.update_button.clicked.connect(self.check_for_updates)
        self.layout.addWidget(self.update_button)

        self.help_manual_button = QPushButton("Ver Manual de Usuario")
        self.help_manual_button.clicked.connect(self.emit_show_help_manual_signal)
        self.layout.addWidget(self.help_manual_button)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttons.accepted.connect(self.accept)
        self.layout.addWidget(self.buttons)

    def check_for_updates(self):
        QDesktopServices.openUrl(QUrl("https://github.com/stevecode-b/InfoMensajes-Power/releases"))

    def emit_show_help_manual_signal(self):
        self.show_help_manual_requested.emit()
        self.accept()
