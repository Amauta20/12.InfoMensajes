from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt
from urllib.parse import urlparse

class AddServiceDialog(QDialog):
    def __init__(self, initial_name="", initial_url="", initial_icon="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Service")
        self.setModal(True)
        self.setFixedSize(300, 180)

        self.layout = QVBoxLayout(self)

        # Name input
        self.name_label = QLabel("Service Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., My Custom Chat")
        self.name_input.setText(initial_name) # Set initial name
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)

        # URL input
        self.url_label = QLabel("Service URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("e.g., https://chat.example.com")
        self.url_input.setText(initial_url) # Set initial URL
        self.url_input.setReadOnly(bool(initial_url)) # Make URL read-only if pre-filled
        self.layout.addWidget(self.url_label)
        self.layout.addWidget(self.url_input)

        # Icon (not directly editable in this dialog, but passed through)
        self.initial_icon = initial_icon

        # Buttons
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addStretch()

        self.layout.addLayout(self.button_layout)

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Service Name cannot be empty.")
            return
        if not url:
            QMessageBox.warning(self, "Input Error", "Service URL cannot be empty.")
            return

        # Basic URL validation
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            QMessageBox.warning(self, "Input Error", "Please enter a valid URL (e.g., https://example.com).")
            return

        self.accept()

    def get_service_data(self):
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        return name, url, self.initial_icon # Return icon as well
