from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QListWidget, QListWidgetItem, QLineEdit, QDialog, QMenu, QGroupBox, QPushButton, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QSize, QDateTime, pyqtSignal as Signal
from PyQt6.QtGui import QColor, QFont, QAction

from app.db.kanban_manager import KanbanManager
from app.db import settings_manager, database
from app.utils import time_utils, report_utils
from app.ui.edit_kanban_card_dialog import EditKanbanCardDialog
from app.ui.view_kanban_card_details_dialog import ViewKanbanCardDetailsDialog
from app.ui.add_kanban_card_dialog import AddKanbanCardDialog
from app.ui.gantt_chart_widget import GanttChartWidget

class KanbanWidget(QWidget):
    kanban_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = database.get_db_connection()
        self.manager = KanbanManager(self.conn)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

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
        self.all_kanban_columns = self.manager.get_all_columns() # Cache columns for context menu

        self.manager.create_default_columns() # Ensure default columns exist
        self.load_kanban_boards()

        self.kanban_layout.addWidget(self.kanban_columns_widget)

        self.buttons_layout = QHBoxLayout()
        self.clear_completed_button = QPushButton("Limpiar Tarjetas Completadas")
        self.clear_completed_button.clicked.connect(self.clear_completed_kanban_cards)
        self.buttons_layout.addWidget(self.clear_completed_button)

        self.gantt_button = QPushButton("Ver Gantt")
        self.gantt_button.clicked.connect(self.open_gantt_chart)
        self.buttons_layout.addWidget(self.gantt_button)

        self.generate_report_button = QPushButton("Generar Reporte")
        self.generate_report_button.clicked.connect(self.generate_kanban_report_ui)
        self.buttons_layout.addWidget(self.generate_report_button)

        self.kanban_layout.addLayout(self.buttons_layout)

        self.layout.addWidget(self.kanban_group_box)

        self.layout.addStretch() # Push content to top
        
    def open_gantt_chart(self):
        self.gantt_chart_widget = GanttChartWidget()
        self.gantt_chart_widget.show()

    def generate_kanban_report_ui(self):
        report_data = self.manager.generate_kanban_report()
        if report_data:
            file_name, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte Kanban", "kanban_report.xlsx", "Excel Files (*.xlsx)")
            if file_name:
                try:
                    report_utils.generate_excel_report(report_data, file_name)
                    QMessageBox.information(self, "Reporte Generado", f"El reporte de Kanban ha sido generado exitosamente en:\n{file_name}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error al generar el reporte de Excel: {e}")
        else:
            QMessageBox.information(self, "Reporte Kanban", "No se encontraron tarjetas Kanban para el reporte.")

    def filter_kanban_cards(self, text):
        search_text = text.lower()
        for column_id, card_list in self.kanban_columns.items():
            for i in range(card_list.count()):
                item = card_list.item(i)
                full_title = item.data(Qt.ItemDataRole.UserRole + 1).lower()
                full_description = item.data(Qt.ItemDataRole.UserRole + 2).lower() if item.data(Qt.ItemDataRole.UserRole + 2) else ""

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

        columns = self.manager.get_all_columns()
        for column in columns:
            column_widget = QWidget()
            column_layout = QVBoxLayout(column_widget)
            column_layout.setContentsMargins(0, 0, 0, 0)
            column_layout.setSpacing(2)

            column_title = QLabel(column['name'])
            column_layout.addWidget(column_title)

            card_list = QListWidget()
            card_list.setMinimumHeight(250)
            card_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card_list.customContextMenuRequested.connect(lambda pos, cl=card_list, col_id=column['id']: self.show_kanban_card_context_menu(pos, cl, col_id))
            card_list.itemDoubleClicked.connect(self.edit_kanban_card)
            column_layout.addWidget(card_list)
            self.kanban_columns[column['id']] = card_list

            if column['name'] == "Por Hacer": # Only allow adding to 'Por Hacer'
                add_card_button = QPushButton("Añadir Tarjeta")
                add_card_button.clicked.connect(lambda checked, col_id=column['id']: self.add_kanban_card(col_id))
                column_layout.addWidget(add_card_button)

            self.kanban_columns_layout.addWidget(column_widget, 1)
            self.load_kanban_cards(column['id'], column['name'])

    def load_kanban_cards(self, column_id, column_name):
        card_list = self.kanban_columns[column_id]
        card_list.clear()
        cards = self.manager.get_cards_by_column(column_id)
        for card in cards:
            assignee_value = card['assignee'] if card['assignee'] else "N/A"
            
            due_date_value = "N/A"
            if card['due_date']:
                utc_dt = QDateTime.fromString(card['due_date'], Qt.DateFormat.ISODate)
                local_dt = utc_dt.toLocalTime()
                due_date_value = local_dt.toString("dd/MM/yyyy HH:mm")

            def format_datetime(dt_str):
                if not dt_str: return "N/A"
                # Convert ISO string to QDateTime, then to Python datetime in local timezone, then format
                qdt = QDateTime.fromString(dt_str, Qt.DateFormat.ISODate)
                dt_obj = time_utils.datetime_from_qdatetime(qdt)
                return time_utils.format_datetime(dt_obj)

            if column_name == "Por Hacer":
                item_text = (
                    f"{card['title']}\n"
                    f"Entregar: {assignee_value} | {due_date_value}"
                )
            elif column_name == "En Progreso":
                item_text = (
                    f"{card['title']}\n"
                    f"Entregar: {assignee_value} | {due_date_value}\n"
                    f"Iniciado: {format_datetime(card['started_at'])}"
                )
            else: # Assuming other columns are 'Done' or similar
                item_text = (
                    f"{card['title']}\n"
                    f"Encargado: {assignee_value} {due_date_value}\n"
                    f"Iniciada: {format_datetime(card['started_at'])}\n"
                    f"Finalizada: {format_datetime(card['finished_at'])}"
                )
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, card['id']) # Store card_id in item data
            item.setData(Qt.ItemDataRole.UserRole + 1, card['title']) # Store full title for filtering
            item.setData(Qt.ItemDataRole.UserRole + 2, card['description']) # Store full description for filtering
            item.setData(Qt.ItemDataRole.UserRole + 3, card['created_at'])
            item.setData(Qt.ItemDataRole.UserRole + 4, card['started_at'])
            item.setData(Qt.ItemDataRole.UserRole + 5, card['finished_at'])
            item.setData(Qt.ItemDataRole.UserRole + 6, card['assignee'])
            item.setData(Qt.ItemDataRole.UserRole + 7, card['due_date'])
            card_list.addItem(item)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            # Set background color based on column
            if column_name == "Por Hacer":
                item.setBackground(QColor(settings_manager.get_todo_color()))
            elif column_name == "En Progreso":
                item.setBackground(QColor(settings_manager.get_inprogress_color()))
            else: # Assuming other columns are 'Done' or similar
                item.setBackground(QColor(settings_manager.get_done_color()))

            item.setForeground(QColor("#FFFFFF")) # White text
            item.setFont(QFont("Segoe UI", 10))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            card_list.setStyleSheet("QListWidget::item { border-bottom: 1px solid #555555; padding: 5px; }")

    def add_kanban_card(self, column_id):
        dialog = AddKanbanCardDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, description, assignee, due_date_qdt = dialog.get_card_data()
            if title:
                due_date_str = due_date_qdt.toUTC().toString(Qt.DateFormat.ISODate) if due_date_qdt else None
                self.manager.create_card(column_id, title, description, assignee, due_date_str, created_at=time_utils.datetime_from_qdatetime(time_utils.get_current_qdatetime()))
                self.load_kanban_boards() # Refresh all boards
                self.kanban_updated.emit()

    def show_kanban_card_context_menu(self, pos, list_widget, current_column_id):
        item = list_widget.itemAt(pos)

        if item:
            card_id = item.data(Qt.ItemDataRole.UserRole) # Retrieve card_id directly
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
        card_details = self.manager.get_card_details(card_id)
        if card_details:
            dialog = ViewKanbanCardDetailsDialog(card_details, self)
            dialog.exec()

    def move_kanban_card(self, card_id, new_column_id):
        self.manager.move_card(card_id, new_column_id)
        self.load_kanban_boards() # Refresh all boards
        self.kanban_updated.emit()

    def delete_kanban_card(self, card_id):
        self.manager.delete_card(card_id)
        self.load_kanban_boards() # Refresh all boards
        self.kanban_updated.emit()

    def clear_completed_kanban_cards(self):
        completed_column_id = None
        for col in self.all_kanban_columns:
            if col['name'] == "Realizadas":
                completed_column_id = col['id']
                break

        if completed_column_id is not None:
            cards_to_delete = self.manager.get_cards_by_column(completed_column_id)
            for card in cards_to_delete:
                self.manager.delete_card(card['id'])
            self.load_kanban_boards() # Refresh all boards
            self.kanban_updated.emit()

    def edit_kanban_card(self, item):
        card_id = item.data(Qt.ItemDataRole.UserRole)
        if card_id is None: return

        card_details = self.manager.get_card_details(card_id)
        if not card_details: return

        dialog = EditKanbanCardDialog(card_details['title'], card_details['description'], card_details['assignee'], card_details['due_date'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_title, new_description, new_assignee, new_due_date_qdt = dialog.get_new_data()
            if new_title:
                new_due_date_str = new_due_date_qdt.toUTC().toString(Qt.DateFormat.ISODate) if new_due_date_qdt else None
                if (new_title != card_details['title'] or 
                    new_description != card_details['description'] or 
                    new_assignee != card_details['assignee'] or 
                    new_due_date_str != card_details['due_date']):
                    self.manager.update_card(card_id, new_title, new_description, new_assignee, new_due_date_str)
                    self.load_kanban_boards()
                    self.kanban_updated.emit()

    def find_and_highlight_card(self, card_id):
        for column_list in self.kanban_columns.values():
            for i in range(column_list.count()):
                item = column_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == card_id:
                    column_list.setCurrentItem(item)
                    return
