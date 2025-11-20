from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QStackedWidget, QToolBar, QLineEdit, QDialog, QPushButton
from PyQt6.QtGui import QAction
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
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.conn = container.conn
        self.metrics_manager = container.metrics_manager
        self.vault_manager = container.vault_manager

        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'fa-solid-900.ttf'))
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)
        else:
            print(f"Font Awesome file not found at: {font_path}")

        # 1. Get core data managers and services from container
        self.settings_manager_instance = container.settings_manager
        self.service_manager_instance = container.service_manager
        self.search_manager_instance = container.search_manager
        self.kanban_manager_instance = container.kanban_manager
        self.notes_manager_instance = container.notes_manager
        self.checklist_manager_instance = container.checklist_manager
        self.reminders_manager = container.reminders_manager
        self.kanban_service_instance = container.kanban_service
        self.notes_service_instance = container.notes_service
        self.checklist_service_instance = container.checklist_service
        self.reminders_service_instance = container.reminders_service
        self.rules_manager = container.rules_manager
        self.templates_manager = container.templates_manager
        self.theme_manager = container.theme_manager

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
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2e2e2e;
                border-bottom: 1px solid #3a3a3a;
                spacing: 5px;
                padding: 2px;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #f0f0f0;
                border: 1px solid #555;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)

        toolbar_container = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 10, 0)
        toolbar_layout.setSpacing(5)
        
        # Global Search
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Buscar...")
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                color: #f0f0f0;
                border: 1px solid #555;
                padding: 3px 5px;
                border-radius: 3px;
                font-size: 12px;
            }
        """)
        self.search_input.returnPressed.connect(self.perform_global_search)
        toolbar_layout.addWidget(self.search_input)
        
        # Pomodoro Widget
        self.pomodoro_widget = PomodoroWidget(self.settings_manager_instance, self.notification_manager)
        self.pomodoro_widget.focus_mode_toggled.connect(self.toggle_focus_mode)
        toolbar_layout.addWidget(self.pomodoro_widget)
        
        toolbar_layout.addStretch()

        # Metrics Button
        self.metrics_button = QPushButton("Métricas")
        self.metrics_button.clicked.connect(self.open_metrics_dashboard)
        toolbar_layout.addWidget(self.metrics_button)

        # AI Assistant Button
        self.ai_button = QPushButton("Asistente IA")
        self.ai_button.clicked.connect(self.toggle_ai_assistant)
        toolbar_layout.addWidget(self.ai_button)
        
        # Theme Button
        self.theme_button = QPushButton("Tema")
        self.theme_button.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_button)

        # Settings Button
        self.general_settings_button = QPushButton("Configuración")
        self.general_settings_button.clicked.connect(self.open_unified_settings_dialog)
        toolbar_layout.addWidget(self.general_settings_button)

        # Help Button
        self.help_button = QPushButton("Ayuda")
        self.help_button.clicked.connect(self.open_about_dialog)
        toolbar_layout.addWidget(self.help_button)
        
        self.toolbar.addWidget(toolbar_container)

    def toggle_focus_mode(self, enabled):
        if enabled:
            self.sidebar.hide()
            self.statusBar().showMessage("Modo Enfoque Activado: Barra lateral oculta.", 5000)
        else:
            self.sidebar.show()
            self.statusBar().showMessage("Modo Enfoque Desactivado.", 3000)

    def toggle_ai_assistant(self):
        if not hasattr(self, 'ai_dock'):
            from PyQt6.QtWidgets import QDockWidget
            from app.ui.executive_assistant_widget import ExecutiveAssistantWidget
            
            self.ai_dock = QDockWidget("Asistente Ejecutivo", self)
            self.ai_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
            self.ai_widget = ExecutiveAssistantWidget(self)
            self.ai_dock.setWidget(self.ai_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_dock)
        
        if self.ai_dock.isVisible():
            self.ai_dock.hide()
        else:
            self.ai_dock.show()

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        new_theme = self.theme_manager.toggle_theme()
        self.statusBar().showMessage(f"Tema cambiado a: {new_theme}", 3000)


    def open_metrics_dashboard(self):
        from app.ui.metrics_dashboard import MetricsDashboard
        dialog = QDialog(self)
        dialog.setWindowTitle("Tablero de Productividad")
        dialog.setMinimumSize(800, 600)
        layout = QVBoxLayout(dialog)
        dashboard = MetricsDashboard(self.metrics_manager)
        layout.addWidget(dashboard)
        dialog.exec()

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
        
        # Pomodoro signals
        self.pomodoro_widget.pomodoro_finished.connect(self.handle_pomodoro_finished)

    def closeEvent(self, event):
        self.metrics_manager.stop_tracking_current()
        super().closeEvent(event)

    def open_unified_settings_dialog(self):
        dialog = UnifiedSettingsDialog(self.settings_manager_instance, self.rules_manager, self.templates_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Ensure Kanban widget exists before loading
            if not getattr(self.workspace_manager, 'kanban_widget', None):
                self.workspace_manager.show_kanban_tools()
            else:
                self.workspace_manager.kanban_widget.load_kanban_boards()
            # Ensure Checklist widget exists before loading
            if not getattr(self.workspace_manager, 'checklist_widget', None):
                self.workspace_manager.show_checklist_tools()
            else:
                self.workspace_manager.checklist_widget.load_kanban_cards()
                self.workspace_manager.checklist_widget.load_independent_checklists()
            # Ensure Agenda widget exists before loading
            if not getattr(self.workspace_manager, 'agenda_widget', None):
                self.workspace_manager.show_agenda_tools()
            else:
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

    def handle_pomodoro_finished(self, mode):
        # Evaluate rules for 'pomodoro_finished' trigger
        actions = self.rules_manager.evaluate_trigger('pomodoro_finished', {'mode': mode})
        for action in actions:
            self.execute_automation_action(action)

    def execute_automation_action(self, action):
        action_type = action['type']
        params = action['params']
        
        if action_type == 'show_notification':
            self.notification_manager.show_notification("Automatización", params.get('message', 'Regla ejecutada'))
        elif action_type == 'open_url':
            import webbrowser
            url = params.get('url')
            if url: webbrowser.open(url)
        elif action_type == 'play_sound':
            # Placeholder for sound playing
            print(f"Playing sound: {params.get('sound')}")
