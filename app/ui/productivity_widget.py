from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QListWidget, QListWidgetItem, QLineEdit, QDialog, QMenu, QGroupBox, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo # Import ZoneInfo for dynamic timezone handling

def convert_utc_to_local(utc_timestamp_str):
    if not utc_timestamp_str:
        return "N/A"
    try:
        # Handle multiple possible formats, including with milliseconds
        if '.' in utc_timestamp_str:
            utc_dt = datetime.strptime(utc_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        else:
            utc_dt = datetime.strptime(utc_timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        # Get local timezone dynamically
        local_tz = datetime.now().astimezone().tzinfo
        local_dt = utc_dt.astimezone(local_tz)
        
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return utc_timestamp_str # Return original string if parsing fails

def format_timestamp_to_local_display(timestamp_str):
    if not timestamp_str:
        return "N/A"
    try:
        # Assuming timestamp_str is in YYYY-MM-DD HH:MM:SS format (from DB)
        if '.' in timestamp_str:
            utc_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        else:
            utc_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        # Get local timezone dynamically
        local_tz = datetime.now().astimezone().tzinfo
        local_dt = utc_dt.astimezone(local_tz)
        
        return local_dt.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):
        return timestamp_str # Return original string if parsing fails


from app.db import notes_manager
from app.db import kanban_manager
from app.ui.edit_note_dialog import EditNoteDialog
from app.ui.edit_kanban_card_dialog import EditKanbanCardDialog
from app.ui.view_kanban_card_details_dialog import ViewKanbanCardDetailsDialog
from app.ui.add_kanban_card_dialog import AddKanbanCardDialog

class NoteInput(QTextEdit):
    def __init__(self, parent):
        super().__init__()
        self.parent_widget = parent # Reference to ProductivityWidget
        self.setPlaceholderText("Crear nueva nota... (Ctrl+Enter)")
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
        self.notes_group_box = QGroupBox("Notas Rápidas")
        self.notes_group_box.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; margin-top: 1ex;} QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px;}")
        self.notes_layout = QVBoxLayout(self.notes_group_box)

        self.note_input = NoteInput(self)
        self.notes_layout.addWidget(self.note_input)

        self.add_note_button = QPushButton("Añadir Nota")
        self.add_note_button.clicked.connect(self.add_note_from_input)
        self.notes_layout.addWidget(self.add_note_button)

        self.note_search_input = QLineEdit()
        self.note_search_input.setPlaceholderText("Buscar notas...")
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
        self.kanban_group_box = QGroupBox("Tablero Kanban")
        self.kanban_group_box.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; margin-top: 1ex;} QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px;}")
        self.kanban_layout = QVBoxLayout(self.kanban_group_box)

        self.kanban_search_input = QLineEdit()
        self.kanban_search_input.setPlaceholderText("Buscar tarjetas Kanban...")
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

        self.clear_completed_button = QPushButton("Limpiar Tarjetas Completadas")
        self.clear_completed_button.clicked.connect(self.clear_completed_kanban_cards)
        self.kanban_layout.addWidget(self.clear_completed_button)

        self.layout.addWidget(self.kanban_group_box)



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
        original_content = item.data(Qt.UserRole + 1)

        dialog = EditNoteDialog(original_content, self)
        if dialog.exec() == QDialog.Accepted:
            new_content = dialog.get_new_content()
            if new_content and new_content != original_content:
                notes_manager.update_note(note_id, new_content)
                self.load_notes()

    def show_note_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)

        if item:
            note_id = item.data(Qt.UserRole)
            if note_id is None: return

            menu = QMenu(self)
            delete_action = QAction("Eliminar Nota", self)
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
            timestamp = format_timestamp_to_local_display(note['updated_at'])
            item_text = f"{snippet} ({timestamp})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, note['id']) # Store note_id in item data
            item.setData(Qt.UserRole + 1, note['content']) # Store full content for editing and filtering
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
            card_list.customContextMenuRequested.connect(lambda pos, cl=card_list, col_id=column['id']: self.show_kanban_card_context_menu(pos, cl, col_id))
            card_list.itemDoubleClicked.connect(self.edit_kanban_card)
            column_layout.addWidget(card_list)
            self.kanban_columns[column['id']] = card_list

            if column['name'] == "Por Hacer": # Only allow adding to 'Por Hacer'
                add_card_button = QPushButton("Añadir Tarjeta")
                add_card_button.clicked.connect(lambda checked, col_id=column['id']: self.add_kanban_card(col_id))
                column_layout.addWidget(add_card_button)

            self.kanban_columns_layout.addWidget(column_widget)
            self.load_kanban_cards(column['id'], column['name'])

    def load_kanban_cards(self, column_id, column_name):
        card_list = self.kanban_columns[column_id]
        card_list.clear()
        cards = kanban_manager.get_cards_by_column(column_id)
        for card in cards:
            assignee_value = card['assignee'] if card['assignee'] else "N/A"
            due_date_value = format_timestamp_to_local_display(card['due_date']) if card['due_date'] else "N/A"
            
            if column_name == "Por Hacer":
                item_text = (f"{card['title']}\n" 
                             f"Entregar: {assignee_value} | {due_date_value}")
            elif column_name == "En Progreso":
                item_text = (f"{card['title']}\n" 
                             f"Entregar: {assignee_value} | {due_date_value}\n" 
                             f"Iniciado: {format_timestamp_to_local_display(card['started_at'])}")
            else:
                item_text = (f"{card['title']}\n" 
                             f"Encargado: {assignee_value} {due_date_value}\n" 
                             f"Creada: {format_timestamp_to_local_display(card['created_at'])}\n" 
                             f"Iniciada: {format_timestamp_to_local_display(card['started_at'])}\n" 
                             f"Finalizada: {format_timestamp_to_local_display(card['finished_at'])}")
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, card['id']) # Store card_id in item data
            item.setData(Qt.UserRole + 1, card['title']) # Store full title for filtering
            item.setData(Qt.UserRole + 2, card['description']) # Store full description for filtering
            item.setData(Qt.UserRole + 3, card['created_at'])
            item.setData(Qt.UserRole + 4, card['started_at'])
            item.setData(Qt.UserRole + 5, card['finished_at'])
            item.setData(Qt.UserRole + 6, card['assignee'])
            item.setData(Qt.UserRole + 7, card['due_date'])
            card_list.addItem(item)

    def add_kanban_card(self, column_id):
        dialog = AddKanbanCardDialog(self)
        if dialog.exec() == QDialog.Accepted:
            title, description, assignee, due_date = dialog.get_card_data()
            if title:
                kanban_manager.create_card(column_id, title, description, assignee, due_date)
                self.load_kanban_boards() # Refresh all boards

    def show_kanban_card_context_menu(self, pos, list_widget, current_column_id):
        item = list_widget.itemAt(pos)

        if item:
            card_id = item.data(Qt.UserRole) # Retrieve card_id directly
            if card_id is None: return # Should not happen

            menu = QMenu(self)

            # Move actions
            move_menu = menu.addMenu("Mover a...")
            for col in self.all_kanban_columns:
                if col['id'] != current_column_id:
                    action = QAction(col['name'], self)
                    action.triggered.connect(lambda checked, c_id=card_id, new_col_id=col['id']: self.move_kanban_card(c_id, new_col_id))
                    move_menu.addAction(action)
            
            # View Details action
            view_action = QAction("Ver Detalles", self)
            view_action.triggered.connect(lambda checked, c_id=card_id: self.view_kanban_card_details(c_id))
            menu.addAction(view_action)

            # Delete action
            delete_action = QAction("Eliminar Tarjeta", self)
            delete_action.triggered.connect(lambda checked, c_id=card_id: self.delete_kanban_card(c_id))
            menu.addAction(delete_action)

            menu.exec(list_widget.mapToGlobal(pos))

    def view_kanban_card_details(self, card_id):
        card_details = kanban_manager.get_card_details(card_id)
        if card_details:
            dialog = ViewKanbanCardDetailsDialog(card_details, self)
            dialog.exec()

    def move_kanban_card(self, card_id, new_column_id):
        kanban_manager.move_card(card_id, new_column_id)
        self.load_kanban_boards() # Refresh all boards

    def delete_kanban_card(self, card_id):
        kanban_manager.delete_card(card_id)
        self.load_kanban_boards() # Refresh all boards

    def clear_completed_kanban_cards(self):
        completed_column_id = None
        for col in self.all_kanban_columns:
            if col['name'] == "Realizadas":
                completed_column_id = col['id']
                break

        if completed_column_id is not None:
            cards_to_delete = kanban_manager.get_cards_by_column(completed_column_id)
            for card in cards_to_delete:
                kanban_manager.delete_card(card['id'])
            self.load_kanban_boards() # Refresh all boards

    def edit_kanban_card(self, item):
        card_id = item.data(Qt.UserRole)
        if card_id is None: return

        card_details = kanban_manager.get_card_details(card_id)
        if not card_details: return

        dialog = EditKanbanCardDialog(card_details['title'], card_details['description'], card_details['assignee'], card_details['due_date'], self)
        if dialog.exec() == QDialog.Accepted:
            new_title, new_description, new_assignee, new_due_date = dialog.get_new_data()
            if new_title and (new_title != card_details['title'] or 
                             new_description != card_details['description'] or 
                             new_assignee != card_details['assignee'] or 
                             new_due_date != card_details['due_date']):
                kanban_manager.update_card(card_id, new_title, new_description, new_assignee, new_due_date)
                self.load_kanban_boards()