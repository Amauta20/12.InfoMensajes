from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class RssArticleItemWidget(QWidget):
    def __init__(self, title, published, summary, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)

        self.title_label = QLabel(f"<b>{title}</b>")
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label)

        self.published_label = QLabel(published)
        self.published_label.setStyleSheet("font-size: 10px; color: gray;")
        self.layout.addWidget(self.published_label)

        self.summary_label = QLabel(summary)
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 12px;")
        self.layout.addWidget(self.summary_label)

        self.layout.addStretch(1)
