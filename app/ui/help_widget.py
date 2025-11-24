from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import os

class HelpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        self.load_help_manual()

    def load_help_manual(self):
        # Modified to load from filesystem
        help_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'help_manual.html'))
        if not os.path.exists(help_path):
             # Fallback for different execution contexts
             help_path = os.path.abspath(os.path.join(os.getcwd(), 'assets', 'help_manual.html'))
        
        self.web_view.setUrl(QUrl.fromLocalFile(help_path))
