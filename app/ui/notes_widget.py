from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QListWidget, QListWidgetItem, QLineEdit, QDialog, QMenu, QGroupBox, QPushButton
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal as Signal
from PyQt6.QtGui import QAction
from app.utils import time_utils
from app.db import settings_manager

from app.db import notes_manager
from app.ui.edit_note_dialog import EditNoteDialog

class NoteInput(QTextEdit):
    def __init__(self, parent):
        super().__init__()
        self.parent_widget = parent # Reference to NotesWidget
        self.setPlaceholderText("Crear nueva nota... (Ctrl+Enter)")
        self.setFixedHeight(60)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.parent_widget.add_note_from_input()
            return
        super().keyPressEvent(event)

class NotesWidget(QWidget):
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
        self.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self.show_note_context_menu)
        self.notes_list.itemDoubleClicked.connect(self.edit_note)

        self.notes_layout.addWidget(self.notes_list)
        self.load_notes()

        self.layout.addWidget(self.notes_group_box)

        self.layout.addStretch() # Push content to top

    def add_note_from_input(self):
        content = self.note_input.toPlainText().strip()
        if content:
            notes_manager.create_note(content)
            self.note_input.clear()
            self.load_notes()

    # --- Note Management Methods ---
    def edit_note(self, item):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        original_content = item.data(Qt.ItemDataRole.UserRole + 1)

        dialog = EditNoteDialog(original_content, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_content = dialog.get_new_content()
            if new_content and new_content != original_content:
                notes_manager.update_note(note_id, new_content)
                self.load_notes()

    def show_note_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)

        if item:
            note_id = item.data(Qt.ItemDataRole.UserRole)
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
            
            timestamp = ""
            if note['updated_at']:
                utc_dt = QDateTime.fromString(note['updated_at'], Qt.DateFormat.ISODate)
                utc_dt.setTimeSpec(Qt.TimeSpec.UTC)
                local_dt = utc_dt.toLocalTime()
                timestamp = local_dt.toString(time_utils.convert_strftime_to_qt_format(settings_manager.get_datetime_format()))

            item_text = f"{snippet} ({timestamp})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, note['id']) # Store note_id in item data
            item.setData(Qt.ItemDataRole.UserRole + 1, note['content']) # Store full content for editing and filtering
            self.notes_list.addItem(item)

    def filter_notes(self, text):
        search_text = text.lower()
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            full_content = item.data(Qt.ItemDataRole.UserRole + 1).lower()
            if search_text in full_content:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def find_and_select_note(self, note_id):
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == note_id:
                self.notes_list.setCurrentItem(item)
                break
