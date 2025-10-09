from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QStackedWidget, QToolBar, QLineEdit, QDialog, QSystemTrayIcon, QPushButton
from PyQt6.QtCore import Qt, QUrl, QTimer, QDateTime
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
import os

from app.ui.sidebar import Sidebar
from app.search import search_manager
from app.db import reminders_manager, checklist_manager, settings_manager, kanban_manager
from app.utils import time_utils
from app.ui.search_results_widget import SearchResultsWidget
from app.ui.styles import dark_theme_stylesheet, light_theme_stylesheet
from app.services import service_manager
from app.ui.welcome_widget import WelcomeWidget
from app.ui.add_service_dialog import AddServiceDialog # Needed for opening dialog from welcome widget
from app.ui.notes_widget import NotesWidget
from app.ui.kanban_widget import KanbanWidget
from app.ui.gantt_chart_widget import GanttChartWidget
from app.ui.checklist_widget import ChecklistWidget
from app.ui.reminders_widget import RemindersWidget
from app.ui.pomodoro_widget import PomodoroWidget
from app.ui.rss_reader_widget import RssReaderWidget
from app.ui.vault_widget import VaultWidget
from app.metrics.metrics_manager import MetricsManager

from app.ui.select_service_dialog import SelectServiceDialog
from app.ui.unified_settings_dialog import UnifiedSettingsDialog

class MainWindow(QMainWindow):
    def __init__(self, metrics_manager_instance):
        super().__init__()
        self.metrics_manager = metrics_manager_instance
        self.setWindowTitle("InfoMensajero")
        self.setGeometry(100, 100, 1280, 720)

        # Main layout
        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Header (Toolbar) ---
        self.toolbar = self.addToolBar("Barra de Herramientas Principal")
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Búsqueda Global (Notas, Kanban, Texto Pegado)")
        self.search_input.setFixedWidth(300)
        self.search_input.returnPressed.connect(self.perform_global_search)
        self.toolbar.addWidget(self.search_input)

        self.toolbar.addSeparator()

        self.pomodoro_widget = PomodoroWidget()
        self.toolbar.addWidget(self.pomodoro_widget)

        self.general_settings_button = QPushButton("Configuración General")
        self.general_settings_button.clicked.connect(self.open_unified_settings_dialog)
        self.toolbar.addWidget(self.general_settings_button)

        # Global Search Shortcut (Ctrl+F)
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.focus_search_bar)

        # --- Web view management ---
        self.web_view_stack = QStackedWidget()
        self.web_views = {} # Cache for web views: {profile_path: QWebEngineView}

        # Search Results Widget
        self.search_results_widget = SearchResultsWidget()
        self.web_view_stack.addWidget(self.search_results_widget) # Add it to the stack, but not visible initially

        # Welcome Widget
        self.welcome_widget = WelcomeWidget()
        self.welcome_widget.add_service_requested.connect(self.add_service_from_welcome)
        self.web_view_stack.addWidget(self.welcome_widget)

        # Notes Widget
        self.notes_widget = NotesWidget()
        self.web_view_stack.addWidget(self.notes_widget)

        # Kanban Widget
        self.kanban_widget = KanbanWidget()
        self.web_view_stack.addWidget(self.kanban_widget)

        # Gantt Chart Widget
        self.gantt_chart_widget = GanttChartWidget()
        self.web_view_stack.addWidget(self.gantt_chart_widget)

        # Checklist Widget
        self.checklist_widget = ChecklistWidget()
        self.web_view_stack.addWidget(self.checklist_widget)

        # Reminders Widget
        self.reminders_widget = RemindersWidget()
        self.web_view_stack.addWidget(self.reminders_widget)

        # RSS Reader Widget
        self.rss_reader_widget = RssReaderWidget()
        self.web_view_stack.addWidget(self.rss_reader_widget)

        # Vault Widget
        self.vault_widget = VaultWidget()
        self.web_view_stack.addWidget(self.vault_widget)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(240)

        # Splitter to manage sidebar and web_view_stack
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.web_view_stack)
        self.splitter.setSizes([240, 1040]) # Sidebar width, main content width

        self.main_layout.addWidget(self.splitter)
        self.setCentralWidget(self.central_widget)

        # Connect signals
        self.sidebar.service_selected.connect(self.load_service)
        self.sidebar.service_deleted.connect(self.remove_webview_for_service)
        self.sidebar.show_notes_requested.connect(self.show_notes_tools)
        self.sidebar.show_kanban_requested.connect(self.show_kanban_tools)
        self.sidebar.show_gantt_chart_requested.connect(self.show_gantt_chart_tools)
        self.sidebar.show_checklist_requested.connect(self.show_checklist_tools)
        self.sidebar.show_reminders_requested.connect(self.show_reminders_tools)
        self.sidebar.show_rss_reader_requested.connect(self.show_rss_reader_tools)
        self.sidebar.show_vault_requested.connect(self.show_vault_tools)

        # Welcome widget signals
        self.welcome_widget.show_kanban_requested.connect(self.show_kanban_tools)
        self.welcome_widget.show_checklist_requested.connect(self.show_checklist_tools)
        self.welcome_widget.show_reminders_requested.connect(self.show_reminders_tools)

        # Productivity widget update signals
        self.kanban_widget.kanban_updated.connect(self.welcome_widget.refresh)
        self.checklist_widget.checklist_updated.connect(self.welcome_widget.refresh)
        self.reminders_widget.reminders_updated.connect(self.welcome_widget.refresh)

        self.kanban_widget.kanban_updated.connect(self.checklist_widget.refresh_kanban_cards)
        self.kanban_widget.kanban_updated.connect(self.gantt_chart_widget.refresh_gantt) # Sync Kanban -> Gantt

        self.search_results_widget.result_clicked.connect(self.on_search_result_clicked)

        # Notification system
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icon.png'))
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.show()

        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_for_notifications)
        self.notification_timer.start(10000) # Check every 10 seconds

        # Load initial service or a default page
        self.load_initial_page()

        # Start tracking initial page
        self.metrics_manager.start_tracking("Bienvenida") # Start tracking Welcome widget

    def closeEvent(self, event):
        self.metrics_manager.stop_tracking_current()
        super().closeEvent(event)

    def show_notification(self, title, message):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)

    def check_for_notifications(self):
        # Get pre-notification offset
        pre_notification_offset_minutes = settings_manager.get_pre_notification_offset()

        # Check for pre-due reminders
        pre_due_reminders = reminders_manager.get_pre_due_reminders(pre_notification_offset_minutes)
        for reminder in pre_due_reminders:
            self.show_notification("Recordatorio Próximo", f"'{reminder['text']}' vence pronto ({reminder['due_at']})")
            reminders_manager.update_reminder(reminder['id'], pre_notified_at=time_utils.to_utc(time_utils.datetime_from_qdatetime(time_utils.get_current_qdatetime())).isoformat())

        # Check for pre-due checklist items
        pre_due_checklist_items = checklist_manager.get_pre_due_checklist_items(pre_notification_offset_minutes)
        for item in pre_due_checklist_items:
            self.show_notification("Tarea de Checklist Próxima", f"'{item['text']}' vence pronto ({item['due_at']})")
            checklist_manager.update_checklist_item(item['id'], pre_notified_at=time_utils.to_utc(time_utils.datetime_from_qdatetime(time_utils.get_current_qdatetime())).isoformat())

        # Check for due reminders
        due_reminders = reminders_manager.get_actual_due_reminders()
        for reminder in due_reminders:
            self.show_notification("Recordatorio", reminder['text'])
            reminders_manager.update_reminder(reminder['id'], is_notified=1)

        # Check for due checklist items
        due_checklist_items = checklist_manager.get_actual_due_checklist_items()
        for item in due_checklist_items:
            self.show_notification("Tarea de Checklist", item['text'])
            checklist_manager.update_checklist_item(item['id'], is_notified=1)

    def show_pomodoro_notification(self, mode):
        if mode == "Pomodoro":
            title = "¡Tiempo de descanso!"
            message = "¡Buen trabajo! Tomate un descanso corto."
        else:
            title = "¡De vuelta al trabajo!"
            message = "El descanso ha terminado. ¡A concentrarse!"
        self.show_notification(title, message)

    def open_unified_settings_dialog(self):
        dialog = UnifiedSettingsDialog(self)
        if dialog.exec():
            # Reload settings that might affect UI or timers
            self.pomodoro_widget.load_settings()
            self.pomodoro_widget.reset_timer()
            # Potentially refresh checklist/reminder views if date format changes
            self.checklist_widget.load_checklist_items() # Assuming this refreshes display
            self.reminders_widget.load_reminders() # Assuming this refreshes display
            self.kanban_widget.load_kanban_boards()

    def show_notes_tools(self):
        self.web_view_stack.setCurrentWidget(self.notes_widget)
        self.track_current_widget_usage()

    def show_kanban_tools(self):
        self.web_view_stack.setCurrentWidget(self.kanban_widget)
        self.track_current_widget_usage()

    def show_gantt_chart_tools(self):
        self.web_view_stack.setCurrentWidget(self.gantt_chart_widget)
        self.gantt_chart_widget.refresh_gantt() # Trigger initial load
        self.track_current_widget_usage()

    def show_checklist_tools(self):
        self.web_view_stack.setCurrentWidget(self.checklist_widget)
        self.track_current_widget_usage()

    def show_reminders_tools(self):
        self.web_view_stack.setCurrentWidget(self.reminders_widget)
        self.track_current_widget_usage()

    def show_rss_reader_tools(self):
        self.web_view_stack.setCurrentWidget(self.rss_reader_widget)
        self.track_current_widget_usage()
        self.track_current_widget_usage()

    def show_vault_tools(self):
        self.web_view_stack.setCurrentWidget(self.vault_widget)
        self.track_current_widget_usage()

    def track_current_widget_usage(self):
        current_widget = self.web_view_stack.currentWidget()
        service_name = "Desconocido"

        if isinstance(current_widget, QWebEngineView):
            # For web views, try to get the service name from the URL or profile
            # This is a simplified approach; a more robust one would map profile_path back to service name
            for profile_path, view in self.web_views.items():
                if view == current_widget:
                    service_details = service_manager.get_service_by_profile_path(profile_path)
                    if service_details: service_name = service_details['name']
                    break
        elif hasattr(current_widget, '__class__'):
            # For internal widgets, use their class name or a predefined name
            if current_widget == self.welcome_widget: service_name = "Bienvenida"
            elif current_widget == self.notes_widget: service_name = "Notas"
            elif current_widget == self.kanban_widget: service_name = "Kanban"
            elif current_widget == self.gantt_chart_widget: service_name = "Gantt"
            elif current_widget == self.checklist_widget: service_name = "Checklist"
            elif current_widget == self.reminders_widget: service_name = "Recordatorios"
            elif current_widget == self.rss_reader_widget: service_name = "Lector RSS"
            elif current_widget == self.vault_widget: service_name = "Bóveda"
            elif current_widget == self.search_results_widget: service_name = "Búsqueda"
            # Add other internal widgets here

        self.metrics_manager.start_tracking(service_name)

    def show_productivity_tools(self):
        # This method is now obsolete, but kept for compatibility until sidebar is fully refactored
        self.web_view_stack.setCurrentWidget(self.notes_widget) # Default to notes for now

    def trigger_add_service_dialog(self):
        self.sidebar.open_select_service_dialog()

    def add_service_from_welcome(self, name, url, icon):
        service_manager.add_service(name, url, icon)
        self.sidebar.load_services()
        self.load_initial_page()

    def focus_search_bar(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def perform_global_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        results = search_manager.search_all(query)
        self.search_results_widget.display_results(results, query)
        self.web_view_stack.setCurrentWidget(self.search_results_widget)
        self.track_current_widget_usage()

    def on_search_result_clicked(self, result_data):
        result_type = result_data.get('type')
        result_id = result_data.get('id')

        if result_type == 'note':
            self.web_view_stack.setCurrentWidget(self.notes_widget)
            self.notes_widget.find_and_select_note(result_id)
        elif result_type == 'kanban_card':
            self.web_view_stack.setCurrentWidget(self.kanban_widget)
            self.kanban_widget.find_and_highlight_card(result_id)

    def load_service(self, url, profile_path):
        """
        Loads a service in its own profile and view, creating it if it doesn't exist.
        """
        if profile_path in self.web_views:
            view = self.web_views[profile_path]
        else:
            # Create a new profile and view for this service
            profile_name = os.path.basename(profile_path) # Use folder name as profile name
            profile = QWebEngineProfile(profile_name, self)
            profile.setPersistentStoragePath(profile_path) # Set the actual storage path
            # Spoof user agent to a recent Chrome version for better compatibility
            profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            view = QWebEngineView()
            view.setPage(QWebEnginePage(profile, view)) # Create a page with the profile and set it to the view
            view.setUrl(QUrl(url))
            
            self.web_views[profile_path] = view
            self.web_view_stack.addWidget(view)

        self.web_view_stack.setCurrentWidget(view)

    def remove_webview_for_service(self, service_id):
        # Find the profile_path associated with the service_id
        service_details = service_manager.get_service_by_id(service_id)
        if not service_details: return

        profile_path = service_details['profile_path']

        if profile_path in self.web_views:
            view_to_remove = self.web_views.pop(profile_path) # Remove from cache
            self.web_view_stack.removeWidget(view_to_remove) # Remove from stack
            view_to_remove.deleteLater() # Schedule for deletion

            # If the removed view was the current one, switch to a default view
            if self.web_view_stack.currentWidget() == view_to_remove:
                self.load_initial_page() # Reload initial page (welcome or first service)

    def load_initial_page(self):
        """
        Loads the first service in the list or a default welcome page.
        """
        services = service_manager.get_all_services()
        if services:
            first_service = services[0]
            self.load_service(first_service['url'], first_service['profile_path'])
        else:
            # If no services, show welcome widget
            self.web_view_stack.setCurrentWidget(self.welcome_widget)