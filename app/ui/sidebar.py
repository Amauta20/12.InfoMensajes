from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QMenu
from PyQt6.QtCore import pyqtSignal as Signal, Qt
from PyQt6.QtGui import QIcon, QAction
from app.services.service_manager import ServiceManager # Changed import
from app.ui.add_service_dialog import AddServiceDialog
from app.ui.edit_service_name_dialog import EditServiceNameDialog
from app.ui.select_service_dialog import SelectServiceDialog

class Sidebar(QWidget):
    service_selected = Signal(str, str) # Signal to emit URL and profile_path
    service_deleted = Signal(int) # Signal to emit service_id when a service is deleted
    show_notes_requested = Signal() # New signal to show NotesWidget
    show_kanban_requested = Signal() # New signal to show KanbanWidget
    show_gantt_chart_requested = Signal() # New signal to show GanttChartWidget
    show_checklist_requested = Signal() # New signal to show ChecklistWidget
    show_reminders_requested = Signal() # New signal to show RemindersWidget
    show_rss_reader_requested = Signal() # New signal to show RssReaderWidget
    show_vault_requested = Signal()
    show_audio_player_requested = Signal()

    def __init__(self, service_manager_instance, parent=None):
        super().__init__(parent)
        self.service_manager = service_manager_instance # Store instance
        self._unread_statuses = {} # {service_id: True/False}
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # --- Services Section ---
        self.services_title = QLabel("Servicios")
        self.layout.addWidget(self.services_title)

        self.add_service_button = QPushButton("Añadir Servicio")
        self.add_service_button.clicked.connect(self.open_select_service_dialog)
        self.layout.addWidget(self.add_service_button)

        # Container for service buttons
        self.services_container = QWidget()
        self.services_layout = QVBoxLayout(self.services_container)
        self.services_layout.setContentsMargins(0, 0, 0, 0)
        self.services_layout.setSpacing(5)
        self.layout.addWidget(self.services_container)

        self.load_services()

        self.layout.addStretch() # Push services to top

        # --- Productivity Tools Buttons ---
        self.notes_button = QPushButton("Notas")
        self.notes_button.clicked.connect(self.show_notes_requested.emit)
        self.layout.addWidget(self.notes_button)

        self.kanban_button = QPushButton("Kanban")
        self.kanban_button.clicked.connect(self.show_kanban_requested.emit)
        self.layout.addWidget(self.kanban_button)

        self.gantt_chart_button = QPushButton("Diagrama de Gantt")
        self.gantt_chart_button.clicked.connect(self.show_gantt_chart_requested.emit)
        self.layout.addWidget(self.gantt_chart_button)

        self.checklist_button = QPushButton("Checklist")
        self.checklist_button.clicked.connect(self.show_checklist_requested.emit)
        self.layout.addWidget(self.checklist_button)

        self.reminders_button = QPushButton("Recordatorios")
        self.reminders_button.clicked.connect(self.show_reminders_requested.emit)
        self.layout.addWidget(self.reminders_button)

        self.rss_reader_button = QPushButton("Lector RSS")
        self.rss_reader_button.clicked.connect(self.show_rss_reader_requested.emit)
        self.layout.addWidget(self.rss_reader_button)

        self.vault_button = QPushButton("Bóveda")
        self.vault_button.clicked.connect(self.show_vault_requested.emit)
        self.layout.addWidget(self.vault_button)

        self.audio_player_button = QPushButton("Reproductor de Audio")
        self.audio_player_button.clicked.connect(self.show_audio_player_requested.emit)
        self.layout.addWidget(self.audio_player_button)

    # --- Service Management Methods ---
    def open_select_service_dialog(self):
        dialog = SelectServiceDialog(self)
        dialog.catalog_service_selected.connect(self._add_catalog_service)
        dialog.custom_service_requested.connect(self._add_custom_service)
        dialog.exec()

    def _add_catalog_service(self, name, url, icon, unread_script):
        self.service_manager.add_service(name, url, icon, unread_script=unread_script)
        self.load_services() # Refresh the service list

    def _add_custom_service(self):
        dialog = AddServiceDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, url, icon = dialog.get_service_data()
            if name and url:
                self.service_manager.add_service(name, url, icon)
                self.load_services() # Refresh the service list

    def load_services(self):
        # Clear existing service buttons from the dedicated layout
        while self.services_layout.count():
            child = self.services_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        services = self.service_manager.get_user_services()

        self._unread_statuses = {s['id']: self._unread_statuses.get(s['id'], False) for s in services} # Preserve existing unread statuses

        for service in services:
            btn = QPushButton(service['name'])
            btn.setProperty('service_id', service['id']) # Store service_id in button property
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, b=btn: self.show_service_context_menu(pos, b))

            # Apply unread style if applicable
            if self._unread_statuses.get(service['id'], False):
                btn.setProperty('class', 'unread') # Apply CSS class

            url = service['url']
            profile_path = service['profile_path']
            btn.clicked.connect(lambda checked=False, u=url, p=profile_path: self.service_selected.emit(u, p))
            self.services_layout.addWidget(btn)

    def show_service_context_menu(self, pos, button):
        service_id = button.property('service_id')
        if service_id is None: return

        menu = QMenu(self)

        add_instance_action = QAction("Añadir Otra Instancia", self)
        add_instance_action.triggered.connect(lambda checked, s_id=service_id: self.add_another_instance_from_ui(s_id))
        menu.addAction(add_instance_action)

        edit_action = QAction("Editar Nombre del Servicio", self)
        edit_action.triggered.connect(lambda checked, s_id=service_id: self.edit_service_name_from_ui(s_id))
        menu.addAction(edit_action)

        delete_action = QAction("Eliminar Servicio", self)
        delete_action.triggered.connect(lambda checked, s_id=service_id: self.delete_service_from_ui(s_id))
        menu.addAction(delete_action)

        menu.exec(button.mapToGlobal(pos))

    def add_another_instance_from_ui(self, service_id):
        service_details = self.service_manager.get_service_by_id(service_id)
        if not service_details: return

        suggested_name = f"{service_details['name']} (Nueva Instancia)"
        dialog = AddServiceDialog(suggested_name, service_details['url'], service_details['icon'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, url, icon = dialog.get_service_data()
            if name and url:
                self.service_manager.add_service(name, url, icon)
                self.load_services() # Refresh the service list

    def edit_service_name_from_ui(self, service_id):
        service_details = self.service_manager.get_service_by_id(service_id)
        if not service_details: return

        dialog = EditServiceNameDialog(service_details['name'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.get_new_name()
            if new_name and new_name != service_details['name']:
                self.service_manager.update_service_name(service_id, new_name)
                self.load_services() # Refresh the service list

    def delete_service_from_ui(self, service_id):
        self.service_manager.delete_service(service_id)
        self.load_services() # Refresh the service list
        self.service_deleted.emit(service_id) # Notify MainWindow to remove webview

    def set_service_unread_status(self, service_id, has_unread):
        if service_id in self._unread_statuses:
            self._unread_statuses[service_id] = has_unread
            self.load_services() # Refresh UI to apply/remove unread style
