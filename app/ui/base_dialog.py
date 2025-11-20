from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QLayout, QWidget

class BaseDialog(QDialog):
    """
    A base class for common dialogs in the application.
    It provides a standard layout with Ok and Cancel buttons.
    """
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Content will be added here by subclasses
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        # Standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

    def add_content(self, layout_or_widget):
        """
        Adds a layout or a widget to the content area of the dialog.
        """
        if isinstance(layout_or_widget, QLayout):
            self.content_layout.addLayout(layout_or_widget)
        elif isinstance(layout_or_widget, QWidget):
            self.content_layout.addWidget(layout_or_widget)
        else:
            raise TypeError(f"Argument must be a QLayout or QWidget, not {type(layout_or_widget).__name__}")

    def validate_and_accept(self):
        """
        Placeholder for validation logic. Subclasses should override this.
        By default, it just accepts the dialog.
        """
        self.accept()
