from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from app.services import service_manager

class SelectServiceDialog(QDialog):
    # Signals to indicate what action was chosen
    catalog_service_selected = pyqtSignal(str, str, str, object) # name, url, icon, unread_script
    custom_service_requested = pyqtSignal() # No args

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Servicio")
        self.setModal(True)
        self.setFixedSize(400, 500)

        self.layout = QVBoxLayout(self)

        self.title_label = QLabel("Elige un Servicio o Añade Personalizado")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        # Catalog List
        self.catalog_list = QListWidget()
        self.catalog_list.itemDoubleClicked.connect(self._on_catalog_item_double_clicked)
        self.layout.addWidget(self.catalog_list)

        self.load_catalog_services()

        # Action Buttons
        self.button_layout = QHBoxLayout()
        self.select_button = QPushButton("Seleccionar")
        self.select_button.clicked.connect(self._on_select_button_clicked)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.select_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addStretch()

        self.layout.addLayout(self.button_layout)

    def load_catalog_services(self):
        catalog = service_manager.ServiceManager.load_catalog()
        for service in catalog:
            item = QListWidgetItem(service['name'])
            item.setData(Qt.ItemDataRole.UserRole, service) # Store full service dict
            self.catalog_list.addItem(item)

    def _on_catalog_item_double_clicked(self, item):
        self._on_select_button_clicked()

    def _on_select_button_clicked(self):
        selected_item = self.catalog_list.currentItem()
        if selected_item:
            service_data = selected_item.data(Qt.ItemDataRole.UserRole)
            # Use .get() for safety, providing None if the key doesn't exist
            unread_script = service_data.get('unread_script')
            self.catalog_service_selected.emit(service_data['name'], service_data['url'], service_data['icon'], unread_script)
            self.accept()
        else:
            # Optionally show a warning if nothing is selected
            pass
