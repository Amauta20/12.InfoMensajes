from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ProductivityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.placeholder_label = QLabel("Productivity tools will be here.")
        self.layout.addWidget(self.placeholder_label)

        self.layout.addStretch()