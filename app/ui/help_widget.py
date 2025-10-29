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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        help_file_path = os.path.join(current_dir, '..', '..', 'assets', 'help_manual.html')
        self.web_view.setUrl(QUrl.fromLocalFile(help_file_path))
