from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
import re

class SearchResultsWidget(QWidget):
    result_clicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        self.title_label = QLabel("Resultados de Búsqueda")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_result_clicked)
        self.layout.addWidget(self.results_list)

    def display_results(self, results, query):
        self.results_list.clear()
        self.title_label.setText(f'Resultados de Búsqueda para: "{query}"')

        if not results:
            self.results_list.addItem("No se encontraron resultados.")
            return

        # Group results by type
        grouped_results = {}
        for result in results:
            result_type = result['type']
            if result_type not in grouped_results:
                grouped_results[result_type] = []
            grouped_results[result_type].append(result)

        type_names = {
            'note': 'Notas',
            'kanban_card': 'Tarjetas Kanban',
            'message': 'Mensajes'
        }

        for result_type, items in grouped_results.items():
            # Add a header for the group
            header_item = QListWidgetItem()
            header_label = QLabel(f'<b>{type_names.get(result_type, result_type.capitalize())}</b>')
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.results_list.addItem(header_item)
            self.results_list.setItemWidget(header_item, header_label)

            for result in items:
                item = QListWidgetItem()
                self.results_list.addItem(item)
                item.setData(Qt.ItemDataRole.UserRole, dict(result))

                label = QLabel()
                label.setWordWrap(True)
                label.setTextFormat(Qt.TextFormat.RichText)

                if result_type == 'note':
                    content = result['content']
                    highlighted_content = self.highlight_text(content, query)
                    label.setText(highlighted_content)
                elif result_type == 'kanban_card':
                    title = result['title']
                    description = result['description'] if result['description'] else ''
                    # Prioritize highlighting in the title
                    if query.lower() in title.lower():
                        highlighted_title = self.highlight_text(title, query)
                        label.setText(highlighted_title)
                    else:
                        highlighted_description = self.highlight_text(description, query)
                        label.setText(f"{title}<br>{highlighted_description}")
                elif result_type == 'message':
                    content = result['content']
                    highlighted_content = self.highlight_text(content, query)
                    label.setText(f"({result['source']}):<br>{highlighted_content}")
                
                item.setSizeHint(label.sizeHint())
                self.results_list.setItemWidget(item, label)

    def highlight_text(self, text, query):
        if not text or not query:
            return text
        # Use regex for case-insensitive replacement and to find all occurrences
        highlighted_text = re.sub(f'({re.escape(query)})', r'<span style="background-color: yellow; color: black;">\1</span>', text, flags=re.IGNORECASE)
        return highlighted_text

    def on_result_clicked(self, item):
        result_data = item.data(Qt.ItemDataRole.UserRole)
        if result_data:
            self.result_clicked.emit(result_data)
