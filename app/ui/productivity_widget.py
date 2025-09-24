from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QListWidget, QListWidgetItem, QLineEdit, QDialog, QMenu, QGroupBox, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

from app.db import notes_manager
from app.db import kanban_manager
from app.ui.edit_note_dialog import EditNoteDialog
from app.ui.edit_kanban_card_dialog import EditKanbanCardDialog

class NoteInput(QTextEdit):
    def __init__(self, parent):
        super().__init__()
        self.parent_widget = parent # Reference to ProductivityWidget
        self.setPlaceholderText("Create a new note... (Ctrl+Enter)")
        self.setFixedHeight(60)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.parent_widget.add_note_from_input()
            return
        super().keyPressEvent(event)

class ProductivityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # --- Notes Section ---
        self.notes_group_box = QGroupBox("Quick Notes")
        self.notes_group_box.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; margin-top: 1ex;} QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px;}")
        self.notes_layout = QVBoxLayout(self.notes_group_box)

        self.note_input = NoteInput(self)
        self.notes_layout.addWidget(self.note_input)

        self.add_note_button = QPushButton("Add Note")
        self.add_note_button.clicked.connect(self.add_note_from_input)
        self.notes_layout.addWidget(self.add_note_button)

        self.note_search_input = QLineEdit()
        self.note_search_input.setPlaceholderText("Search notes...")
        self.note_search_input.textChanged.connect(self.filter_notes)
        self.notes_layout.addWidget(self.note_search_input)

        self.notes_list = QListWidget()
        self.notes_list.setFixedHeight(200)
        self.notes_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self.show_note_context_menu)
        self.notes_list.itemDoubleClicked.connect(self.edit_note)

        self.notes_layout.addWidget(self.notes_list)
        self.load_notes()

        self.layout.addWidget(self.notes_group_box)

        # --- Kanban Section ---
        self.kanban_group_box = QGroupBox("Kanban Board")
        self.kanban_group_box.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; margin-top: 1ex;} QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px;}")
        self.kanban_layout = QVBoxLayout(self.kanban_group_box)

        self.kanban_search_input = QLineEdit()
        self.kanban_search_input.setPlaceholderText("Search Kanban cards...")
        self.kanban_search_input.textChanged.connect(self.filter_kanban_cards)
        self.kanban_layout.addWidget(self.kanban_search_input)

        self.kanban_columns_widget = QWidget()
        self.kanban_columns_layout = QHBoxLayout(self.kanban_columns_widget)
        self.kanban_columns_layout.setContentsMargins(0, 0, 0, 0)
        self.kanban_columns_layout.setSpacing(5)

        self.kanban_columns = {}
        self.kanban_card_inputs = {}
        self.all_kanban_columns = kanban_manager.get_all_columns() # Cache columns for context menu

        kanban_manager.create_default_columns() # Ensure default columns exist
        self.load_kanban_boards()

        self.kanban_layout.addWidget(self.kanban_columns_widget)

        self.layout.addWidget(self.kanban_group_box)

        # --- Calendar Section ---
        self.calendar_group_box = QGroupBox("Calendar")
        self.calendar_group_box.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; margin-top: 1ex;} QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px;}")
        self.calendar_layout = QVBoxLayout(self.calendar_group_box)

        self.calendar_view = QWebEngineView()
        self.calendar_view.setUrl(QUrl("https://calendar.google.com")) # Default to Google Calendar
        self.calendar_view.setMinimumHeight(400)
        self.calendar_layout.addWidget(self.calendar_view)

        self.layout.addWidget(self.calendar_group_box)

        self.layout.addStretch() # Push content to top

    def add_note_from_input(self):
        content = self.note_input.toPlainText().strip()
        if content:
            notes_manager.create_note(content)
            self.note_input.clear()
            self.load_notes()

    # --- Note Management Methods ---
    def edit_note(self, item):
        note_id = item.data(Qt.UserRole)
        current_content = item.text()

        dialog = EditNoteDialog(current_content, self)
        if dialog.exec() == QDialog.Accepted:
            new_content = dialog.get_new_content()
            if new_content and new_content != current_content:
                notes_manager.update_note(note_id, new_content)
                self.load_notes()

    def show_note_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)

        if item:
            note_id = item.data(Qt.UserRole)
            if note_id is None: return

            menu = QMenu(self)
            delete_action = QAction("Delete Note", self)
            delete_action.triggered.connect(lambda checked, n_id=note_id: self.delete_note_from_ui(n_id))
            menu.addAction(delete_action)

            menu.exec(list_widget.mapToGlobal(pos))

    def delete_note_from_ui(self, note_id):
        notes_manager.delete_note(note_id)
        self.load_notes()

    def load_notes(self):
        self.notes_list.clear()
        notes = notes_manager.get_all_notes()
        for note in notes:
            snippet = note['content'].split('\n')[0] # First line as snippet
            timestamp = note['updated_at']
            item_text = f"{snippet} ({timestamp[:16]})" # Show YYYY-MM-DD HH:MM
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, note['id']) # Store note_id in item data
            item.setData(Qt.UserRole + 1, note['content']) # Store full content for filtering
            self.notes_list.addItem(item)

    def filter_notes(self, text):
        search_text = text.lower()
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            full_content = item.data(Qt.UserRole + 1).lower()
            if search_text in full_content:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def filter_kanban_cards(self, text):
        search_text = text.lower()
        for column_id, card_list in self.kanban_columns.items():
            for i in range(card_list.count()):
                item = card_list.item(i)
                full_title = item.data(Qt.UserRole + 1).lower()
                full_description = item.data(Qt.UserRole + 2).lower() if item.data(Qt.UserRole + 2) else ""

                if search_text in full_title or search_text in full_description:
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    # --- Kanban Methods ---
    def load_kanban_boards(self):
        # Clear existing columns
        for i in reversed(range(self.kanban_columns_layout.count())):
            widget = self.kanban_columns_layout.itemAt(i).widget()
            if widget: widget.deleteLater()

        self.kanban_columns.clear()
        self.kanban_card_inputs.clear()

        columns = kanban_manager.get_all_columns()
        for column in columns:
            column_widget = QWidget()
            column_layout = QVBoxLayout(column_widget)
            column_layout.setContentsMargins(0, 0, 0, 0)
            column_layout.setSpacing(2)

            column_title = QLabel(column['name'])
            column_layout.addWidget(column_title)

            card_list = QListWidget()
            card_list.setMinimumHeight(100)
            card_list.setContextMenuPolicy(Qt.CustomContextMenu)
            card_list.customContextMenuRequested.connect(lambda pos, col_id=column['id']: self.show_kanban_card_context_menu(pos, col_id))
            card_list.itemDoubleClicked.connect(self.edit_kanban_card)
            column_layout.addWidget(card_list)
            self.kanban_columns[column['id']] = card_list

            if column['name'] == "Por Hacer": # Only allow adding to 'Por Hacer'
                card_input = QLineEdit()
                card_input.setPlaceholderText("Add new card...")
                card_input.returnPressed.connect(lambda col_id=column['id'], input_field=card_input: self.add_kanban_card(col_id, input_field))
                column_layout.addWidget(card_input)
                self.kanban_card_inputs[column['id']] = card_input

            self.kanban_columns_layout.addWidget(column_widget)
            self.load_kanban_cards(column['id'])

    def load_kanban_cards(self, column_id):
        card_list = self.kanban_columns[column_id]
        card_list.clear()
        cards = kanban_manager.get_cards_by_column(column_id)
        for card in cards:
            item = QListWidgetItem(card['title'])
            item.setData(Qt.UserRole, card['id']) # Store card_id in item data
            item.setData(Qt.UserRole + 1, card['title']) # Store full title for filtering
            item.setData(Qt.UserRole + 2, card['description']) # Store full description for filtering
            card_list.addItem(item)

    def add_kanban_card(self, column_id, input_field):
        title = input_field.text().strip()
        if title:
            kanban_manager.create_card(column_id, title)
            input_field.clear()
            self.load_kanban_cards(column_id)

    def show_kanban_card_context_menu(self, pos, current_column_id):
        list_widget = self.sender() # The QListWidget that sent the signal
        item = list_widget.itemAt(pos)

        if item:
            card_id = item.data(Qt.UserRole) # Retrieve card_id directly
            if card_id is None: return # Should not happen

            menu = QMenu(self)

            # Move actions
            move_menu = menu.addMenu("Move to...")
            for col in self.all_kanban_columns:
                if col['id'] != current_column_id:
                    action = QAction(col['name'], self)
                    action.triggered.connect(lambda checked, c_id=card_id, new_col_id=col['id']: self.move_kanban_card(c_id, new_col_id))
                    move_menu.addAction(action)
            
            # Delete action
            delete_action = QAction("Delete Card", self)
            delete_action.triggered.connect(lambda checked, c_id=card_id: self.delete_kanban_card(c_id))
            menu.addAction(delete_action)

            menu.exec(list_widget.mapToGlobal(pos))

    def move_kanban_card(self, card_id, new_column_id):
        kanban_manager.move_card(card_id, new_column_id)
        self.load_kanban_boards() # Refresh all boards

    def delete_kanban_card(self, card_id):
        kanban_manager.delete_card(card_id)
        self.load_kanban_boards() # Refresh all boards

    def edit_kanban_card(self, item):
        card_id = item.data(Qt.UserRole)
        if card_id is None: return

        card_details = kanban_manager.get_card_details(card_id)
        if not card_details: return

        dialog = EditKanbanCardDialog(card_details['title'], card_details['description'], self)
        if dialog.exec() == QDialog.Accepted:
            new_title, new_description = dialog.get_new_data()
            if new_title and (new_title != card_details['title'] or new_description != card_details['description']):
                kanban_manager.update_card(card_id, new_title, new_description)
                self.load_kanban_boards()
