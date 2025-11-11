from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QStackedWidget, QToolBar, QLineEdit, QDialog, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import os

from app.ui.sidebar import Sidebar
from app.db.reminders_manager import RemindersManager
from app.db.checklist_manager import ChecklistManager
from app.db.settings_manager import SettingsManager
from app.db.kanban_manager import KanbanManager
from app.db.notes_manager import NotesManager
from app.services_layer.kanban_service import KanbanService
from app.services_layer.notes_service import NotesService
from app.services_layer.checklist_service import ChecklistService
from app.services_layer.reminders_service import RemindersService
from app.services.service_manager import ServiceManager
from app.security.vault_manager import VaultManager
from app.search.search_manager import SearchManager
from app.ui.webview_manager import WebViewManager
from app.ui.shortcut_manager import ShortcutManager
from app.ui.notification_manager import NotificationManager
from app.ui.workspace_manager import WorkspaceManager

from app.ui.pomodoro_widget import PomodoroWidget
from app.ui.unified_settings_dialog import UnifiedSettingsDialog
from app.ui.about_dialog import AboutDialog
from PyQt6.QtGui import QFontDatabase

class MainWindow(QMainWindow):
    def __init__(self, conn, metrics_manager_instance, vault_manager_instance):
        super().__init__()
        self.conn = conn
        self.metrics_manager = metrics_manager_instance
        self.vault_manager = vault_manager_instance

        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'fa-solid-900.ttf'))
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)
        else:
            print(f"Font Awesome file not found at: {font_path}")

        # 1. Instantiate core data managers and services
        self.settings_manager_instance = SettingsManager.get_instance()
        self.service_manager_instance = ServiceManager(self.conn)
        self.search_manager_instance = SearchManager(self.conn)
        self.kanban_manager_instance = KanbanManager(self.conn)
        self.notes_manager_instance = NotesManager(self.conn)
        self.checklist_manager_instance = ChecklistManager(self.conn)
        self.reminders_manager = RemindersManager(self.conn)
        self.kanban_service_instance = KanbanService(self.kanban_manager_instance)
        self.notes_service_instance = NotesService(self.notes_manager_instance)
        self.checklist_service_instance = ChecklistService(self.checklist_manager_instance)
        self.reminders_service_instance = RemindersService(self.reminders_manager, self.kanban_service_instance, self.checklist_service_instance)

        self.setWindowTitle("InfoMensajero")
        self.setGeometry(100, 100, 1280, 720)

        # 2. Instantiate NotificationManager (as it's a dependency for the toolbar)
        self.notification_manager = NotificationManager(self, self.settings_manager_instance, self.reminders_service_instance, self.checklist_service_instance)

        # 3. Set up main UI layout components
        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.web_view_stack = QStackedWidget()
        self.sidebar = Sidebar(self.service_manager_instance)
        self.sidebar.setFixedWidth(240)

        # 4. Set up the toolbar (which creates search_input)
        self._setup_toolbar()

        # 5. Instantiate remaining component managers
        self.webview_manager = WebViewManager(self.web_view_stack, self.service_manager_instance, self)
        services = {
            'notes': self.notes_service_instance, 'kanban': self.kanban_service_instance,
            'checklist': self.checklist_service_instance, 'reminders': self.reminders_service_instance,
        }
        managers = {
            'search': self.search_manager_instance, 'settings': self.settings_manager_instance,
            'vault': self.vault_manager,
        }
        self.workspace_manager = WorkspaceManager(self.web_view_stack, self.conn, services, managers, self)
        self.shortcut_manager = ShortcutManager(self, self.search_input, self.web_view_stack)

        # 6. Set up main layout
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.web_view_stack)
        self.splitter.setSizes([240, 1040])
        self.main_layout.addWidget(self.splitter)
        self.setCentralWidget(self.central_widget)

        # 7. Connect signals
        self._connect_signals()

        # 8. Final Setup
        self.workspace_manager.show_welcome_page()
        self.metrics_manager.start_tracking("Bienvenida")

    def _setup_toolbar(self):
        self.toolbar = self.addToolBar("Barra de Herramientas Principal")
        toolbar_container = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 20, 0)
        toolbar_layout.setSpacing(5)
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Búsqueda Global")
        self.search_input.setFixedWidth(300)
        self.search_input.returnPressed.connect(self.perform_global_search)
        toolbar_layout.addWidget(self.search_input)
        
        self.pomodoro_widget = PomodoroWidget(self.settings_manager_instance, self.notification_manager)
        toolbar_layout.addWidget(self.pomodoro_widget)
        
        self.general_settings_button = QPushButton("Configuración General")
        self.general_settings_button.clicked.connect(self.open_unified_settings_dialog)
        toolbar_layout.addWidget(self.general_settings_button)
        
        toolbar_layout.addStretch()
        
        self.help_button = QPushButton("Ayuda")
        self.help_button.clicked.connect(self.open_about_dialog)
        toolbar_layout.addWidget(self.help_button)
        
        self.toolbar.addWidget(toolbar_container)

    def _connect_signals(self):
        # Sidebar signals
        self.sidebar.service_selected.connect(self.webview_manager.load_service)
        self.sidebar.service_deleted.connect(self.handle_service_deleted)
        self.sidebar.show_notes_requested.connect(self.workspace_manager.show_notes_tools)
        self.sidebar.show_kanban_requested.connect(self.workspace_manager.show_kanban_tools)
        self.sidebar.show_gantt_chart_requested.connect(self.workspace_manager.show_gantt_chart_tools)
        self.sidebar.show_checklist_requested.connect(self.workspace_manager.show_checklist_tools)
        self.sidebar.show_reminders_requested.connect(self.workspace_manager.show_agenda_tools)
        self.sidebar.show_rss_reader_requested.connect(self.workspace_manager.show_rss_reader_tools)
        self.sidebar.show_vault_requested.connect(self.workspace_manager.show_vault_tools)
        self.sidebar.show_audio_player_requested.connect(self.workspace_manager.show_audio_player_tools)
        
        # WebViewManager signals
        self.webview_manager.unread_status_changed.connect(self.sidebar.set_service_unread_status)
        self.webview_manager.notification_requested.connect(self.notification_manager.show_notification)

    def closeEvent(self, event):
        self.metrics_manager.stop_tracking_current()
        super().closeEvent(event)

    def open_unified_settings_dialog(self):
        dialog = UnifiedSettingsDialog(self.settings_manager_instance, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.workspace_manager.kanban_widget.load_kanban_boards()
            self.workspace_manager.checklist_widget.load_kanban_cards()
            self.workspace_manager.checklist_widget.load_independent_checklists()
            self.workspace_manager.agenda_widget.load_agenda_items()

    def open_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.show_help_manual_requested.connect(self.workspace_manager.show_help_manual)
        dialog.exec()

    def perform_global_search(self):
        query = self.search_input.text().strip()
        if not query: return
        results = self.search_manager_instance.search_all(query)
        self.workspace_manager.show_search_results(results, query)

    def handle_service_deleted(self, service_id):
        current_view = self.web_view_stack.currentWidget()
        if hasattr(current_view, 'property') and current_view.property('service_id') == service_id:
            self.workspace_manager.show_welcome_page()
        self.webview_manager.remove_webview_for_service(service_id)
