from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QInputDialog, QMessageBox, QListWidgetItem, QCheckBox, QLineEdit, QSplitter, QLabel, QTabWidget, QDateTimeEdit, QDialog, QFormLayout
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal as Signal
from app.db import checklist_manager, kanban_manager, settings_manager
from app.utils import time_utils
import datetime

class AddChecklistItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Item de Checklist")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.item_text_input = QLineEdit()
        self.form_layout.addRow("Texto del Item:", self.item_text_input)

        self.due_date_input = QDateTimeEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(settings_manager.get_datetime_format()))
        self.due_date_input.setMinimumDateTime(time_utils.get_current_qdatetime())
        self.due_date_input.setDateTime(time_utils.get_current_qdatetime())
        self.due_date_input.setEnabled(False) # Initially disabled

        self.enable_due_date_checkbox = QCheckBox("Habilitar Fecha de Vencimiento")
        self.enable_due_date_checkbox.stateChanged.connect(self.due_date_input.setEnabled)

        self.form_layout.addRow("Fecha de Vencimiento:", self.due_date_input)
        self.form_layout.addRow(self.enable_due_date_checkbox)

        self.layout.addLayout(self.form_layout)

        self.buttons = QHBoxLayout()
        self.ok_button = QPushButton("Aceptar")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        self.buttons.addWidget(self.ok_button)
        self.buttons.addWidget(self.cancel_button)
        self.layout.addLayout(self.buttons)

    def getItemData(self):
        text = self.item_text_input.text().strip()
        due_at = None
        if self.enable_due_date_checkbox.isChecked():
            due_at = self.due_date_input.dateTime()
        return text, due_at

class ChecklistWidget(QWidget):
    checklist_updated = Signal()

    def __init__(self):
        super().__init__()
        self.current_checklist_id = None

        self.layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        # Left side: Tab widget with two lists
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar::tab { color: black; }")
        self.left_layout.addWidget(self.tab_widget)

        # Kanban tasks tab
        self.kanban_tasks_widget = QWidget()
        self.kanban_tasks_layout = QVBoxLayout(self.kanban_tasks_widget)
        self.kanban_card_list = QListWidget()
        self.kanban_card_list.itemClicked.connect(self.on_kanban_card_selected)
        self.kanban_tasks_layout.addWidget(self.kanban_card_list)
        self.tab_widget.addTab(self.kanban_tasks_widget, "Tareas de Kanban")

        # Independent checklists tab
        self.independent_checklists_widget = QWidget()
        self.independent_checklists_layout = QVBoxLayout(self.independent_checklists_widget)
        self.independent_checklist_list = QListWidget()
        self.independent_checklist_list.itemClicked.connect(self.on_independent_checklist_selected)
        self.independent_checklists_layout.addWidget(self.independent_checklist_list)
        
        self.add_independent_checklist_button = QPushButton("Nueva Checklist Independiente")
        self.add_independent_checklist_button.clicked.connect(self.add_independent_checklist)
        self.independent_checklists_layout.addWidget(self.add_independent_checklist_button)
        self.tab_widget.addTab(self.independent_checklists_widget, "Checklists Independientes")

        # Right side: Checklist items
        self.checklist_items_widget = QWidget()
        self.checklist_items_layout = QVBoxLayout(self.checklist_items_widget)
        self.checklist_items_label = QLabel("Items de la Checklist")
        self.checklist_items_layout.addWidget(self.checklist_items_label)
        self.checklist_items_list = QListWidget()
        self.checklist_items_layout.addWidget(self.checklist_items_list)

        self.item_buttons_layout = QHBoxLayout()
        self.add_item_button = QPushButton("Nuevo Item")
        self.add_item_button.clicked.connect(self.add_item)
        self.item_buttons_layout.addWidget(self.add_item_button)
        self.checklist_items_layout.addLayout(self.item_buttons_layout)

        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.checklist_items_widget)

        self.load_kanban_cards()
        self.load_independent_checklists()

    def load_kanban_cards(self):
        self.kanban_card_list.clear()
        cards = kanban_manager.get_all_cards()
        for card in cards:
            item = QListWidgetItem(card['title'])
            item.setData(Qt.UserRole, card['id'])
            self.kanban_card_list.addItem(item)

    def load_independent_checklists(self):
        self.independent_checklist_list.clear()
        checklists = checklist_manager.get_independent_checklists()
        for checklist in checklists:
            item = QListWidgetItem(checklist['name'])
            item.setData(Qt.UserRole, checklist['id'])
            self.independent_checklist_list.addItem(item)

    def on_kanban_card_selected(self, item):
        card_id = item.data(Qt.UserRole)
        # A card might have multiple checklists. For now, let's assume one checklist per card.
        # A better approach would be to show a list of checklists for the card.
        checklists = checklist_manager.get_checklists_for_card(card_id)
        if checklists:
            self.current_checklist_id = checklists[0]['id']
            self.checklist_items_label.setText(f"Checklist para: {item.text()}")
            self.load_checklist_items()
        else:
            # If no checklist exists, create one automatically
            checklist_name = f"Checklist para {item.text()}"
            self.current_checklist_id = checklist_manager.create_checklist(checklist_name, card_id)
            self.checklist_items_label.setText(f"Checklist para: {item.text()}")
            self.load_checklist_items()

    def on_independent_checklist_selected(self, item):
        self.current_checklist_id = item.data(Qt.UserRole)
        self.checklist_items_label.setText(f"Checklist: {item.text()}")
        self.load_checklist_items()

    def load_checklist_items(self):
        self.checklist_items_list.clear()
        if self.current_checklist_id:
            checklist = checklist_manager.get_checklist(self.current_checklist_id)
            if not checklist: return
            for item_data in checklist['items']:
                item_widget = self.create_checklist_item_widget(item_data)
                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                self.checklist_items_list.addItem(list_item)
                self.checklist_items_list.setItemWidget(list_item, item_widget)

    def create_checklist_item_widget(self, item_data):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        checkbox = QCheckBox()
        checkbox.setChecked(item_data['is_checked'])
        checkbox.stateChanged.connect(lambda state, item_id=item_data['id']: self.toggle_item_checked(item_id, state))
        layout.addWidget(checkbox)

        item_text = item_data['text']
        if item_data['due_at']:
            utc_dt = QDateTime.fromString(item_data['due_at'], Qt.ISODate)
            local_dt = utc_dt.toLocalTime()
            item_text += f" ({local_dt.toString(time_utils.convert_strftime_to_qt_format(settings_manager.get_datetime_format()))})"

        text_label = QLineEdit(item_text)
        text_label.setReadOnly(True)
        text_label.setStyleSheet("border: none;")

        font = text_label.font()
        font.setStrikeOut(item_data['is_checked'])
        text_label.setFont(font)

        layout.addWidget(text_label)

        delete_button = QPushButton("🗑")
        delete_button.setFixedWidth(30)
        delete_button.clicked.connect(lambda checked=False, item_id=item_data['id']: self.delete_item(item_id))
        layout.addWidget(delete_button)

        return widget

    def add_independent_checklist(self):
        text, ok = QInputDialog.getText(self, 'Nueva Checklist Independiente', 'Nombre de la checklist:')
        if ok and text:
            checklist_manager.create_checklist(text)
            self.load_independent_checklists()
            self.checklist_updated.emit()

    def add_item(self):
        if self.current_checklist_id:
            dialog = AddChecklistItemDialog(self)
            if dialog.exec() == QDialog.Accepted:
                text, due_at_qdt = dialog.getItemData()
                if text:
                    due_at_str = None
                    if due_at_qdt:
                        due_at_str = due_at_qdt.toUTC().toString(Qt.ISODate)
                    checklist_manager.add_item_to_checklist(self.current_checklist_id, text, due_at_str)
                    self.load_checklist_items()
                    self.checklist_updated.emit()

    def delete_item(self, item_id):
        checklist_manager.delete_checklist_item(item_id)
        self.load_checklist_items()
        self.checklist_updated.emit()

    def toggle_item_checked(self, item_id, state):
        is_checked = 1 if state == Qt.Checked else 0
        checklist_manager.update_checklist_item(item_id, is_checked=is_checked)
        self.load_checklist_items()
        self.checklist_updated.emit()

    def update_item_due_date(self, item_id, datetime_qdt):
        # Convert QDateTime to timezone-aware datetime string
        due_at_str = datetime_qdt.toUTC().toString(Qt.ISODate)
        checklist_manager.update_checklist_item(item_id, due_at=due_at_str, is_notified=0)
        self.checklist_updated.emit()

    def refresh_kanban_cards(self):
        self.load_kanban_cards()