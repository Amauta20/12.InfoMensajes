from PyQt6.QtWidgets import QDialog, QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QTimeEdit, QCheckBox, QHBoxLayout, QPushButton, QListWidget, QLabel, QSizePolicy, QTabWidget, QListWidgetItem, QMenu, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtCore import pyqtSignal as Signal

from app.services_layer.checklist_service import ChecklistService
from app.services_layer.kanban_service import KanbanService
from app.db import settings_manager
from app.utils import time_utils
import datetime

# Dialog classes (EditChecklistItemDialog, AddChecklistItemDialog) remain unchanged...
class EditChecklistItemDialog(QDialog):
    def __init__(self, current_text, current_due_date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Item de Checklist")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.item_text_input = QLineEdit(current_text)
        self.form_layout.addRow("Texto del Item:", self.item_text_input)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setMinimumDate(time_utils.get_current_qdatetime().date())

        self.due_time_edit = QTimeEdit()

        self.enable_due_date_checkbox = QCheckBox("Habilitar Fecha de Vencimiento")
        self.enable_due_date_checkbox.stateChanged.connect(self.due_date_edit.setEnabled)
        self.enable_due_date_checkbox.stateChanged.connect(self.due_time_edit.setEnabled)

        if current_due_date:
            self.due_date_edit.setDate(current_due_date.date())
            self.due_time_edit.setTime(current_due_date.time())
            self.enable_due_date_checkbox.setChecked(True)
            self.due_date_edit.setEnabled(True)
            self.due_time_edit.setEnabled(True)
        else:
            self.due_date_edit.setDate(time_utils.get_current_qdatetime().date())
            self.due_time_edit.setTime(time_utils.get_current_qdatetime().time())
            self.due_date_edit.setEnabled(False)
            self.due_time_edit.setEnabled(False)

        due_date_layout = QHBoxLayout()
        due_date_layout.addWidget(self.due_date_edit)
        due_date_layout.addWidget(self.due_time_edit)
        self.form_layout.addRow("Fecha y Hora de Vencimiento:", due_date_layout)
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
            date = self.due_date_edit.date()
            time = self.due_time_edit.time()
            due_at = QDateTime(date, time)
        return text, due_at

class AddChecklistItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Item de Checklist")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.item_text_input = QLineEdit()
        self.form_layout.addRow("Texto del Item:", self.item_text_input)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setMinimumDate(time_utils.get_current_qdatetime().date())
        self.due_date_edit.setDate(time_utils.get_current_qdatetime().date())
        self.due_date_edit.setEnabled(False)

        self.due_time_edit = QTimeEdit()
        self.due_time_edit.setMinimumTime(time_utils.get_current_qdatetime().time())
        self.due_time_edit.setTime(time_utils.get_current_qdatetime().time())
        self.due_time_edit.setEnabled(False)

        self.enable_due_date_checkbox = QCheckBox("Habilitar Fecha de Vencimiento")
        self.enable_due_date_checkbox.stateChanged.connect(self.due_date_edit.setEnabled)
        due_date_layout = QHBoxLayout()
        due_date_layout.addWidget(self.due_date_edit)
        due_date_layout.addWidget(self.due_time_edit)
        self.form_layout.addRow("Fecha y Hora de Vencimiento:", due_date_layout)
        self.form_layout.addRow(self.enable_due_date_checkbox)

        self.layout.addLayout(self.form_layout)

        self.buttons = QHBoxLayout()
        self.ok_button = QPushButton("Aceptar")
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        self.buttons.addWidget(self.ok_button)
        self.buttons.addWidget(self.cancel_button)
        self.layout.addLayout(self.buttons)

    def validate_and_accept(self):
        text = self.item_text_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Error de Entrada", "El texto del item no puede estar vacío.")
            return
        self.accept()

    def getItemData(self):
        text = self.item_text_input.text().strip()
        due_at = None
        if self.enable_due_date_checkbox.isChecked():
            date = self.due_date_edit.date()
            time = self.due_time_edit.time()
            due_at = QDateTime(date, time)
        return text, due_at

class ChecklistWidget(QWidget):
    checklist_updated = Signal()

    def __init__(self, checklist_service: ChecklistService, kanban_service: KanbanService, settings_manager, parent=None):
        super().__init__(parent)
        self.checklist_service = checklist_service
        self.kanban_service = kanban_service
        self.settings_manager = settings_manager
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
        self.kanban_card_list.currentItemChanged.connect(self.on_kanban_card_selected_and_load)
        self.kanban_checklists_layout.addWidget(self.kanban_card_list)

        self.kanban_checklist_items_layout = QVBoxLayout()
        self.checklist_items_label = QLabel("Selecciona una tarjeta Kanban")
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
        self.independent_checklist_list.currentItemChanged.connect(self.on_independent_checklist_selected_and_load)
        self.independent_checklist_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.independent_checklist_list.customContextMenuRequested.connect(self.show_independent_checklist_context_menu)
        self.independent_checklists_layout.addWidget(self.independent_checklist_list)

        self.independent_checklist_items_layout = QVBoxLayout()
        self.independent_checklist_label = QLabel("Selecciona una checklist independiente")
        self.independent_checklist_items_layout.addWidget(self.independent_checklist_label)

        self.independent_checklist_items_list = QListWidget()
        self.independent_checklist_items_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.independent_checklist_items_layout.addWidget(self.independent_checklist_items_list)

        self.add_independent_checklist_button = QPushButton("Añadir Checklist Independiente")
        self.add_independent_checklist_button.clicked.connect(self.add_independent_checklist)
        self.independent_checklist_items_layout.addWidget(self.add_independent_checklist_button)

        self.add_item_independent_button = QPushButton("Añadir Item a Checklist Independiente")
        self.add_item_independent_button.clicked.connect(self.add_item)
        self.independent_checklist_items_layout.addWidget(self.add_item_independent_button)

        self.independent_checklists_layout.addLayout(self.independent_checklist_items_layout)

        from app.ui.styles import dark_theme_stylesheet
        self.setStyleSheet(dark_theme_stylesheet)

        self.load_kanban_cards()
        self.load_independent_checklists()

        if self.kanban_card_list.count() > 0:
            self.kanban_card_list.setCurrentRow(0)
        elif self.independent_checklist_list.count() > 0:
            self.tab_widget.setCurrentIndex(1)
            self.independent_checklist_list.setCurrentRow(0)

    def _add_item_to_list(self, list_widget, item_data, row=None):
        """Creates and adds a single checklist item widget to the list."""
        item_widget = self.create_checklist_item_widget(item_data)
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        list_item.setData(Qt.ItemDataRole.UserRole, item_data['id']) # Store item ID

        if row is not None:
            list_widget.insertItem(row, list_item)
        else:
            list_widget.addItem(list_item)
            
        list_widget.setItemWidget(list_item, item_widget)
        return list_item

    def _find_list_item(self, list_widget, item_id):
        """Finds a QListWidgetItem in a given list widget by its ID."""
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == item_id:
                return item
        return None

    def load_kanban_cards(self):
        self.kanban_card_list.clear()
        cards = self.kanban_service.get_all_cards()
        for card in cards:
            item = QListWidgetItem(card['title'])
            item.setData(Qt.ItemDataRole.UserRole, card['id'])
            self.kanban_card_list.addItem(item)

    def load_independent_checklists(self):
        self.independent_checklist_list.clear()
        checklists = self.checklist_service.get_independent_checklists()
        for checklist in checklists:
            item = QListWidgetItem(checklist['name'])
            item.setData(Qt.ItemDataRole.UserRole, checklist['id'])
            self.independent_checklist_list.addItem(item)

    def on_kanban_card_selected_and_load(self, current, previous):
        list_widget_to_load = self.checklist_items_list
        if not current:
            list_widget_to_load.clear()
            self.checklist_items_label.setText("Selecciona una tarjeta Kanban")
            self.current_checklist_id = None
            return

        card_id = current.data(Qt.ItemDataRole.UserRole)
        self.checklist_items_label.setText(f"Checklist para: {current.text()}")
        checklists = self.checklist_service.get_checklists_for_card(card_id)
        
        if checklists:
            self.current_checklist_id = checklists[0]['id']
        else:
            checklist_name = f"Checklist para {current.text()}"
            self.current_checklist_id = self.checklist_service.create_checklist(checklist_name, card_id)
        
        list_widget_to_load.clear()
        if self.current_checklist_id:
            checklist = self.checklist_service.get_checklist(self.current_checklist_id)
            if checklist and checklist.get('items'):
                for item_data in checklist['items']:
                    self._add_item_to_list(list_widget_to_load, item_data)
            else:
                list_widget_to_load.addItem("No hay ítems en esta checklist.")

    def on_independent_checklist_selected_and_load(self, current, previous):
        list_widget_to_load = self.independent_checklist_items_list
        if not current:
            list_widget_to_load.clear()
            self.independent_checklist_label.setText("Selecciona una checklist independiente")
            self.current_checklist_id = None
            return

        self.current_checklist_id = current.data(Qt.ItemDataRole.UserRole)
        self.independent_checklist_label.setText(f"Checklist: {current.text()}")
        
        list_widget_to_load.clear()
        if self.current_checklist_id:
            checklist = self.checklist_service.get_checklist(self.current_checklist_id)
            if checklist and checklist.get('items'):
                for item_data in checklist['items']:
                    self._add_item_to_list(list_widget_to_load, item_data)
            else:
                list_widget_to_load.addItem("No hay ítems en esta checklist.")

    def show_independent_checklist_context_menu(self, position):
        item = self.independent_checklist_list.itemAt(position)
        if not item: return
        menu = QMenu()
        edit_action = menu.addAction("Editar nombre")
        delete_action = menu.addAction("Eliminar")
        action = menu.exec(self.independent_checklist_list.mapToGlobal(position))
        if action == edit_action: self.edit_independent_checklist_name(item)
        elif action == delete_action: self.delete_independent_checklist(item)

    def edit_independent_checklist_name(self, item):
        checklist_id = item.data(Qt.ItemDataRole.UserRole)
        current_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Editar Nombre de Checklist", "Nuevo nombre:", text=current_name)
        if ok and new_name and new_name != current_name:
            self.checklist_service.update_checklist_name(checklist_id, new_name)
            self.load_independent_checklists()
            self.checklist_updated.emit()

    def delete_independent_checklist(self, item):
        checklist_id = item.data(Qt.ItemDataRole.UserRole)
        checklist_name = item.text()
        reply = QMessageBox.question(self, 'Confirmar Eliminación', 
                                     f"¿Estás seguro de que quieres eliminar la checklist '{checklist_name}' y todos sus ítems?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.checklist_service.delete_checklist(checklist_id)
            self.load_independent_checklists()
            self.independent_checklist_items_list.clear()
            self.independent_checklist_label.setText("Selecciona una checklist independiente")
            self.checklist_updated.emit()

    def create_checklist_item_widget(self, item_data):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        checkbox = QCheckBox()
        checkbox.setChecked(item_data['is_checked'])
        layout.addWidget(checkbox)

        item_display_label = QLabel(item_data['text'])
        font = item_display_label.font()
        font.setStrikeOut(item_data['is_checked'])
        item_display_label.setFont(font)
        layout.addWidget(item_display_label)

        checkbox.stateChanged.connect(lambda state, item_id=item_data['id'], lbl=item_display_label: self.toggle_item_checked(item_id, state, lbl))

        local_dt = None
        if item_data.get('due_at'):
            try:
                utc_dt = QDateTime.fromString(item_data['due_at'], Qt.DateFormat.ISODate)
                if utc_dt.isValid():
                    local_dt = utc_dt.toLocalTime()
                    due_date_text = local_dt.toString(time_utils.convert_strftime_to_qt_format(self.settings_manager.get_datetime_format()))
                    due_date_label = QLabel(f"({due_date_text})")
                    layout.addWidget(due_date_label)
            except Exception as e:
                print(f"Error parsing due_at: {e}")

        layout.addStretch()

        edit_button = QPushButton("\uf044")
        edit_button.setStyleSheet("QPushButton { font-family: \"Font Awesome 6 Free\"; font-size: 12px; padding: 0px; margin: 0px; border: none; }")
        edit_button.setFixedSize(24, 24)
        edit_button.clicked.connect(lambda ch, id=item_data['id'], txt=item_data['text'], due=local_dt: self.edit_checklist_item(id, txt, due))
        layout.addWidget(edit_button)

        delete_button = QPushButton("\uf2ed")
        delete_button.setStyleSheet("QPushButton { font-family: \"Font Awesome 6 Free\"; font-size: 12px; padding: 0px; margin: 0px; border: none; }")
        delete_button.setFixedSize(24, 24)
        delete_button.clicked.connect(lambda ch, id=item_data['id']: self.delete_item(id))
        layout.addWidget(delete_button)

        widget.adjustSize()
        return widget

    def add_independent_checklist(self):
        text, ok = QInputDialog.getText(self, 'Nueva Checklist Independiente', 'Nombre de la checklist:')
        if ok and text:
            new_id = self.checklist_service.create_checklist(text)
            self.load_independent_checklists()
            self.checklist_updated.emit()
            for i in range(self.independent_checklist_list.count()):
                item = self.independent_checklist_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == new_id:
                    self.independent_checklist_list.setCurrentItem(item)
                    break

    def _get_current_checklist_list_widget(self):
        if self.tab_widget.currentIndex() == 0:
            return self.checklist_items_list
        elif self.tab_widget.currentIndex() == 1:
            return self.independent_checklist_items_list
        return None

    def add_item(self):
        if not self.current_checklist_id:
            QMessageBox.information(self, "Seleccionar Checklist", "Por favor, selecciona una checklist antes de añadir un item.")
            return

        dialog = AddChecklistItemDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            text, due_at_qdt = dialog.getItemData()
            if text:
                due_at_str = time_utils.qdatetime_to_utc_iso(due_at_qdt) if due_at_qdt else None
                new_item_id = self.checklist_service.add_item_to_checklist(self.current_checklist_id, text, due_at_str)
                
                # Add to UI without full reload
                current_list_widget = self._get_current_checklist_list_widget()
                if current_list_widget:
                    # This requires a new service method to get a single item's data
                    new_item_data = self.checklist_service.get_checklist_item(new_item_id)
                    if new_item_data:
                        self._add_item_to_list(current_list_widget, new_item_data)

                self.checklist_updated.emit()

    def delete_item(self, item_id):
        reply = QMessageBox.question(self, 'Confirmar Eliminación', '¿Estás seguro de que quieres eliminar este item?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            current_list_widget = self._get_current_checklist_list_widget()
            list_item = self._find_list_item(current_list_widget, item_id)
            
            if list_item:
                self.checklist_service.delete_checklist_item(item_id)
                row = current_list_widget.row(list_item)
                current_list_widget.takeItem(row)
                self.checklist_updated.emit()

    def toggle_item_checked(self, item_id, state, text_label):
        is_checked = 1 if state == Qt.CheckState.Checked.value else 0
        self.checklist_service.update_checklist_item(item_id, is_checked=is_checked)
        font = text_label.font()
        font.setStrikeOut(is_checked)
        text_label.setFont(font)
        self.checklist_updated.emit()

    def edit_checklist_item(self, item_id, current_text, current_due_date):
        dialog = EditChecklistItemDialog(current_text, current_due_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_text, new_due_date_qdt = dialog.getItemData()
            if new_text:
                new_due_date_str = time_utils.qdatetime_to_utc_iso(new_due_date_qdt) if new_due_date_qdt else None
                self.checklist_service.update_checklist_item(item_id, text=new_text, due_at=new_due_date_str)
                
                # Update UI without full reload
                current_list_widget = self._get_current_checklist_list_widget()
                list_item = self._find_list_item(current_list_widget, item_id)
                if list_item:
                    row = current_list_widget.row(list_item)
                    current_list_widget.takeItem(row)
                    updated_item_data = self.checklist_service.get_checklist_item(item_id)
                    if updated_item_data:
                        self._add_item_to_list(current_list_widget, updated_item_data, row)

                self.checklist_updated.emit()

    def refresh_kanban_cards(self):
        self.load_kanban_cards()
