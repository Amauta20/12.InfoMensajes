from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QInputDialog, QMessageBox, QListWidgetItem, QCheckBox, QLineEdit, QSplitter, QLabel, QTabWidget, QDateTimeEdit, QDialog, QFormLayout, QSizePolicy
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal as Signal
from app.db import checklist_manager, kanban_manager, settings_manager
from app.utils import time_utils
import datetime

class EditChecklistItemDialog(QDialog):
    def __init__(self, current_text, current_due_date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Item de Checklist")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.item_text_input = QLineEdit(current_text)
        self.form_layout.addRow("Texto del Item:", self.item_text_input)

        self.due_date_input = QDateTimeEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDisplayFormat(time_utils.convert_strftime_to_qt_format(settings_manager.get_datetime_format()))
        self.due_date_input.setMinimumDateTime(time_utils.get_current_qdatetime())
        
        self.enable_due_date_checkbox = QCheckBox("Habilitar Fecha de Vencimiento")
        self.enable_due_date_checkbox.stateChanged.connect(self.due_date_input.setEnabled)

        if current_due_date:
            self.due_date_input.setDateTime(current_due_date)
            self.enable_due_date_checkbox.setChecked(True)
            self.due_date_input.setEnabled(True)
        else:
            self.due_date_input.setDateTime(time_utils.get_current_qdatetime())
            self.due_date_input.setEnabled(False)

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checklist_manager = checklist_manager
        self.current_checklist_id = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Kanban Checklists Tab
        self.kanban_checklists_tab = QWidget()
        self.kanban_checklists_layout = QHBoxLayout(self.kanban_checklists_tab)
        self.tab_widget.addTab(self.kanban_checklists_tab, "Checklists de Kanban")

        self.kanban_card_list = QListWidget()
        self.kanban_card_list.setFixedWidth(200)
        self.kanban_card_list.itemClicked.connect(self.on_kanban_card_selected)
        self.kanban_checklists_layout.addWidget(self.kanban_card_list)

        self.kanban_checklist_items_layout = QVBoxLayout()
        self.checklist_items_label = QLabel("Selecciona una tarjeta Kanban o una checklist independiente")
        self.kanban_checklist_items_layout.addWidget(self.checklist_items_label)

        self.checklist_items_list = QListWidget()
        self.checklist_items_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.kanban_checklist_items_layout.addWidget(self.checklist_items_list)

        self.add_item_button = QPushButton("Añadir Item")
        self.add_item_button.clicked.connect(self.add_item)
        self.kanban_checklist_items_layout.addWidget(self.add_item_button)

        self.kanban_checklists_layout.addLayout(self.kanban_checklist_items_layout)

        # Independent Checklists Tab
        self.independent_checklists_tab = QWidget()
        self.independent_checklists_layout = QHBoxLayout(self.independent_checklists_tab)
        self.tab_widget.addTab(self.independent_checklists_tab, "Checklists Independientes")

        self.independent_checklist_list = QListWidget()
        self.independent_checklist_list.setFixedWidth(200)
        self.independent_checklist_list.itemClicked.connect(self.on_independent_checklist_selected)
        self.independent_checklists_layout.addWidget(self.independent_checklist_list)

        self.independent_checklist_items_layout = QVBoxLayout()
        self.independent_checklist_items_layout.addWidget(QLabel("Selecciona una checklist independiente"))

        self.independent_checklist_items_list = QListWidget() # Separate list for independent checklists
        self.independent_checklist_items_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.independent_checklist_items_layout.addWidget(self.independent_checklist_items_list)

        self.add_independent_checklist_button = QPushButton("Añadir Checklist Independiente")
        self.add_independent_checklist_button.clicked.connect(self.add_independent_checklist)
        self.independent_checklist_items_layout.addWidget(self.add_independent_checklist_button)

        self.add_item_independent_button = QPushButton("Añadir Item a Checklist Independiente")
        self.add_item_independent_button.clicked.connect(self.add_item) # Reuse add_item for independent checklists
        self.independent_checklist_items_layout.addWidget(self.add_item_independent_button)

        self.independent_checklists_layout.addLayout(self.independent_checklist_items_layout)

        # Apply stylesheet
        from app.ui.styles import dark_theme_stylesheet
        self.setStyleSheet(dark_theme_stylesheet)

        self.load_kanban_cards()
        self.load_independent_checklists()

    def load_kanban_cards(self):
        self.kanban_card_list.clear()
        cards = kanban_manager.get_all_cards()
        for card in cards:
            item = QListWidgetItem(card['title'])
            item.setData(Qt.ItemDataRole.UserRole, card['id'])
            self.kanban_card_list.addItem(item)

    def load_independent_checklists(self):
        self.independent_checklist_list.clear()
        checklists = checklist_manager.get_independent_checklists()
        for checklist in checklists:
            item = QListWidgetItem(checklist['name'])
            item.setData(Qt.ItemDataRole.UserRole, checklist['id'])
            self.independent_checklist_list.addItem(item)

    def load_checklist_items(self):
        current_list_widget = self._get_current_checklist_list_widget()
        if not current_list_widget: return

        current_list_widget.clear()
        if self.current_checklist_id:
            checklist = checklist_manager.get_checklist(self.current_checklist_id)
            if not checklist: return
            for item_data in checklist['items']:
                item_widget = self.create_checklist_item_widget(item_data)
                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                current_list_widget.addItem(list_item)
                current_list_widget.setItemWidget(list_item, item_widget)

    def on_kanban_card_selected(self, item):
        card_id = item.data(Qt.ItemDataRole.UserRole)
        checklists = checklist_manager.get_checklists_for_card(card_id)
        if checklists:
            self.load_checklist_items()
        else:
            checklist_name = f"Checklist para {item.text()}"
            self.current_checklist_id = checklist_manager.create_checklist(checklist_name, card_id)
            self.checklist_items_label.setText(f"Checklist para: {item.text()}")
            self.load_checklist_items()

    def on_independent_checklist_selected(self, item):
        self.current_checklist_id = item.data(Qt.ItemDataRole.UserRole)
        self.checklist_items_label.setText(f"Checklist: {item.text()}")
        self.load_checklist_items()

    def create_checklist_item_widget(self, item_data):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        widget.setStyleSheet("background-color: transparent;")

        item_text = item_data['text']
        text_label = QLineEdit(item_data['text'])
        text_label.setStyleSheet("background-color: transparent; border: none;")
        text_label.editingFinished.connect(lambda item_id=item_data['id'], editor=text_label: self.update_checklist_item_text(item_id, editor.text()))
        
        font = text_label.font()
        font.setStrikeOut(item_data['is_checked'])
        text_label.setFont(font)
        checkbox = QCheckBox()
        checkbox.setStyleSheet("background-color: transparent;")
        checkbox.setChecked(item_data['is_checked'])
        checkbox.stateChanged.connect(lambda state, item_id=item_data['id'], text_label=text_label: self.toggle_item_checked(item_id, state, text_label))
        layout.addWidget(checkbox)

        item_display_label = QLabel(item_data['text'])
        font = item_display_label.font()
        font.setStrikeOut(item_data['is_checked'])
        item_display_label.setFont(font)
        layout.addWidget(item_display_label)

        if item_data['due_at']:
            utc_dt = QDateTime.fromString(item_data['due_at'], Qt.DateFormat.ISODate)
            local_dt = utc_dt.toLocalTime()
            due_date_text = local_dt.toString(time_utils.convert_strftime_to_qt_format(settings_manager.get_datetime_format()))
            due_date_label = QLabel(f"({due_date_text})")
            layout.addWidget(due_date_label)

        edit_button = QPushButton("✏️")
        edit_button.setFixedWidth(30)
        edit_button.clicked.connect(lambda checked, item_id=item_data['id'], current_text=item_data['text'], current_due_date=local_dt if item_data['due_at'] else None: self.edit_checklist_item(item_id, current_text, current_due_date))
        layout.addWidget(edit_button)

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

    def _get_current_checklist_list_widget(self):
        if self.tab_widget.currentIndex() == 0: # Kanban Checklists tab
            return self.checklist_items_list
        elif self.tab_widget.currentIndex() == 1: # Independent Checklists tab
            return self.independent_checklist_items_list
        return None

    def add_item(self):
        if self.current_checklist_id:
            dialog = AddChecklistItemDialog(self)
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                text, due_at_qdt = dialog.getItemData()
                if text:
                    due_at_str = None
                    if due_at_qdt:
                        due_at_str = due_at_qdt.toUTC().toString(Qt.DateFormat.ISODate)
                    checklist_manager.add_item_to_checklist(self.current_checklist_id, text, due_at_str)
                    current_list_widget = self._get_current_checklist_list_widget()
                    if current_list_widget:
                        self.load_checklist_items()
                    self.checklist_updated.emit()

    def delete_item(self, item_id):
        checklist_manager.delete_checklist_item(item_id)
        current_list_widget = self._get_current_checklist_list_widget()
        if current_list_widget:
            self.load_checklist_items()
        self.checklist_updated.emit()

    def toggle_item_checked(self, item_id, state, text_label):
        is_checked = 1 if state == Qt.CheckState.Checked.value else 0
        checklist_manager.update_checklist_item(item_id, is_checked=is_checked)
        font = text_label.font()
        font.setStrikeOut(is_checked)
        text_label.setFont(font)
        self.checklist_updated.emit()

    def edit_checklist_item(self, item_id, current_text, current_due_date):
        dialog = EditChecklistItemDialog(current_text, current_due_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_text, new_due_date_qdt = dialog.getItemData()
            if new_text:
                new_due_date_str = new_due_date_qdt.toUTC().toString(Qt.DateFormat.ISODate) if new_due_date_qdt else None
                checklist_manager.update_checklist_item(item_id, text=new_text, due_at=new_due_date_str)
                current_list_widget = self._get_current_checklist_list_widget()
                if current_list_widget:
                    self.load_checklist_items()
                self.checklist_updated.emit()

    def update_item_due_date(self, item_id, datetime_qdt):
        # This method is no longer used as editing is handled by EditChecklistItemDialog
        pass

    def refresh_kanban_cards(self):
        self.load_kanban_cards()