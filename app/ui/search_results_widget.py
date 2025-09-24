from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QListWidgetItem
from PySide6.QtCore import Qt

class SearchResultsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        self.title_label = QLabel("Search Results")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        self.results_list = QListWidget()
        self.layout.addWidget(self.results_list)

    def display_results(self, results, query):
        self.results_list.clear()
        self.title_label.setText(f"Search Results for: \"{query}\"")

        if not results:
            self.results_list.addItem("No results found.")
            return

        for result in results:
            item_text = ""
            if result['type'] == 'note':
                item_text = f"Note: {result['content'][:100]}..."
            elif result['type'] == 'kanban_card':
                item_text = f"Kanban Card: {result['title']} - {result['description'][:100] if result['description'] else ''}..."
            elif result['type'] == 'message':
                item_text = f"Message ({result['source']}): {result['content'][:100]}..."
            
            item = QListWidgetItem(item_text)
            self.results_list.addItem(item)
