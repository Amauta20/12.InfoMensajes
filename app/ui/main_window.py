from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QStackedWidget, QToolBar, QLineEdit, QApplication, QDialog, QSystemTrayIcon, QPushButton
from PyQt5.QtCore import Qt, QUrl, QTimer, QDateTime
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QStackedWidget, QToolBar, QLineEdit, QApplication, QDialog, QSystemTrayIcon, QPushButton, QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEnginePage
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

from app.ui.select_service_dialog import SelectServiceDialog
from app.ui.unified_settings_dialog import UnifiedSettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(240)

        # Splitter to manage sidebar and web_view_stack
        self.splitter = QSplitter(1, self)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.web_view_stack)

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

        # Welcome widget signals
        self.welcome_widget.show_kanban_requested.connect(self.show_kanban_tools)
        self.welcome_widget.show_checklist_requested.connect(self.show_checklist_tools)
        self.welcome_widget.show_reminders_requested.connect(self.show_reminders_tools)

        # Productivity widget update signals
        self.kanban_widget.kanban_updated.connect(self.welcome_widget.refresh)
        self.checklist_widget.checklist_updated.connect(self.welcome_widget.refresh)
        self.reminders_widget.reminders_updated.connect(self.welcome_widget.refresh)

        self.kanban_widget.kanban_updated.connect(self.checklist_widget.refresh_kanban_cards)

        self.search_results_widget.result_clicked.connect(self.on_search_result_clicked)

        self.pomodoro_widget.pomodoro_finished.connect(self.show_pomodoro_notification)

        # Notification system
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.show()

        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_for_notifications)
        self.notification_timer.start(10000) # Check every 10 seconds

        # Load initial service or a default page
        self.load_initial_page()

    def show_notification(self, title, message):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)

    def check_for_notifications(self):
        # Get pre-notification offset
        pre_notification_offset_minutes = settings_manager.get_pre_notification_offset()

        # Check for pre-due reminders
        pre_due_reminders = reminders_manager.get_pre_due_reminders(pre_notification_offset_minutes)
        for reminder in pre_due_reminders:
            self.show_notification("Recordatorio Próximo", f"'{reminder['text']}' vence pronto ({reminder['due_at']})")
            reminders_manager.update_reminder(reminder['id'], pre_notified_at=time_utils.to_utc(QDateTime.currentDateTime().toPython()).strftime("%Y-%m-%d %H:%M:%S"))

        # Check for pre-due checklist items
        pre_due_checklist_items = checklist_manager.get_pre_due_checklist_items(pre_notification_offset_minutes)
        for item in pre_due_checklist_items:
            self.show_notification("Tarea de Checklist Próxima", f"'{item['text']}' vence pronto ({item['due_at']})")
            checklist_manager.update_checklist_item(item['id'], pre_notified_at=time_utils.to_utc(QDateTime.currentDateTime().toPython()).strftime("%Y-%m-%d %H:%M:%S"))

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

    def show_kanban_tools(self):
        self.web_view_stack.setCurrentWidget(self.kanban_widget)

    def show_gantt_chart_tools(self):
        print("--- Entering show_gantt_chart_tools ---")
        try:
            print("Getting all Kanban cards...")
            kanban_cards = kanban_manager.get_all_cards()
            print(f"Found {len(kanban_cards)} Kanban cards.")

            gantt_tasks = []
            for card in kanban_cards:
                card_start_date = card['started_at']
                card_created_at = card['created_at']
                card_finished_at = card['finished_at']
                card_due_date = card['due_date']

                status = "not_started"
                if card_finished_at:
                    status = "completed"
                elif card_start_date:
                    status = "in_progress"

                effective_start_date = None
                effective_end_date = None

                if status == "not_started":
                    if card_due_date:
                        effective_start_date = card_due_date
                        effective_end_date = card_due_date
                elif status == "in_progress":
                    if card_start_date and card_due_date:
                        effective_start_date = card_start_date
                        effective_end_date = card_due_date
                    elif card_start_date:
                        effective_start_date = card_start_date
                        effective_end_date = QDateTime.currentDateTime().toUTC().toString(Qt.ISODate)
                elif status == "completed":
                    if card_start_date and card_finished_at:
                        effective_start_date = card_start_date
                        effective_end_date = card_finished_at
                    elif card_finished_at:
                        effective_start_date = card_finished_at
                        effective_end_date = card_finished_at

                if effective_start_date and effective_end_date:
                    gantt_tasks.append({
                        'name': card['title'],
                        'start': effective_start_date,
                        'end': effective_end_date,
                        'status': status
                    })
            
            print(f"Formatted Gantt Tasks: {gantt_tasks}")

            gantt_dependencies = []

            print("Loading Gantt chart...")
            self.gantt_chart_widget.load_gantt_chart(gantt_tasks, gantt_dependencies)
            print("Setting current widget to Gantt chart...")
            self.web_view_stack.setCurrentWidget(self.gantt_chart_widget)
            print(f"Current widget in stack: {self.web_view_stack.currentWidget()}")
        except Exception as e:
            print(f"--- ERROR in show_gantt_chart_tools: {e} ---")
        print("--- Exiting show_gantt_chart_tools ---")

    def show_checklist_tools(self):
        self.web_view_stack.setCurrentWidget(self.checklist_widget)

    def show_reminders_tools(self):
        self.web_view_stack.setCurrentWidget(self.reminders_widget)

    def show_rss_reader_tools(self):
        self.web_view_stack.setCurrentWidget(self.rss_reader_widget)

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