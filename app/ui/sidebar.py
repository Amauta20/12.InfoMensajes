from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QMenu
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction
from app.services import service_manager
from app.ui.add_service_dialog import AddServiceDialog
from app.ui.edit_service_name_dialog import EditServiceNameDialog
from app.ui.select_service_dialog import SelectServiceDialog

class Sidebar(QWidget):
    service_selected = Signal(str, str) # Signal to emit URL and profile_path
    service_deleted = Signal(int) # Signal to emit service_id when a service is deleted
    show_productivity_requested = Signal() # New signal to show productivity tools

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # --- Services Section ---
        self.services_title = QLabel("Servicios")
        self.layout.addWidget(self.services_title)

        self.add_service_button = QPushButton("Añadir Servicio")
        self.add_service_button.clicked.connect(self.open_select_service_dialog)
        self.layout.addWidget(self.add_service_button)

        self.load_services()

        self.layout.addStretch() # Push services to top

        # --- Productivity Tools Button ---
        self.productivity_button = QPushButton("Productividad")
        self.productivity_button.clicked.connect(self.show_productivity_requested.emit)
        self.layout.addWidget(self.productivity_button)

    # --- Service Management Methods ---
    def open_select_service_dialog(self):
        dialog = SelectServiceDialog(self)
        dialog.catalog_service_selected.connect(self._add_catalog_service)
        dialog.custom_service_requested.connect(self._add_custom_service)
        dialog.exec()

    def _add_catalog_service(self, name, url, icon):
        service_manager.add_service(name, url, icon)
        self.load_services() # Refresh the service list

    def _add_custom_service(self):
        dialog = AddServiceDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, url, icon = dialog.get_service_data()
            if name and url:
                service_manager.add_service(name, url, icon)
                self.load_services() # Refresh the service list

    def load_services(self):
        # Clear existing service buttons (if any)
        # Iterate in reverse to safely remove widgets from layout
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton) and widget.property('service_id'): 
                widget.deleteLater()

        services = service_manager.get_all_services()
        if not services:
            # Add some default services if the DB is empty
            catalog = service_manager.load_catalog()
            if catalog:
                service_manager.add_service(catalog[0]['name'], catalog[0]['url'], catalog[0]['icon'])
                service_manager.add_service(catalog[1]['name'], catalog[1]['url'], catalog[1]['icon'])
                services = service_manager.get_all_services()

        for service in services:
            btn = QPushButton(service['name'])
            btn.setProperty('service_id', service['id']) # Store service_id in button property
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, b=btn: self.show_service_context_menu(pos, b))

            url = service['url']
            profile_path = service['profile_path']
            btn.clicked.connect(lambda checked=False, u=url, p=profile_path: self.service_selected.emit(u, p))
            self.layout.addWidget(btn)

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
        service_details = service_manager.get_service_by_id(service_id)
        if not service_details: return

        suggested_name = f"{service_details['name']} (Nueva Instancia)"
        dialog = AddServiceDialog(suggested_name, service_details['url'], service_details['icon'], self)
        if dialog.exec() == QDialog.Accepted:
            name, url, icon = dialog.get_service_data()
            if name and url:
                service_manager.add_service(name, url, icon)
                self.load_services() # Refresh the service list

    def edit_service_name_from_ui(self, service_id):
        service_details = service_manager.get_service_by_id(service_id)
        if not service_details: return

        dialog = EditServiceNameDialog(service_details['name'], self)
        if dialog.exec() == QDialog.Accepted:
            new_name = dialog.get_new_name()
            if new_name and new_name != service_details['name']:
                service_manager.update_service_name(service_id, new_name)
                self.load_services() # Refresh the service list

    def delete_service_from_ui(self, service_id):
        service_manager.delete_service(service_id)
        self.load_services() # Refresh the service list
        self.service_deleted.emit(service_id) # Notify MainWindow to remove webview