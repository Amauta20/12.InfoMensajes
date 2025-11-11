from PyQt6.QtCore import QObject
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Imports for all the widgets it will manage
from app.ui.search_results_widget import SearchResultsWidget
from app.ui.welcome_widget import WelcomeWidget
from app.ui.notes_widget import NotesWidget
from app.ui.kanban_widget import KanbanWidget
from app.ui.gantt_chart_widget import GanttChartWidget
from app.ui.checklist_widget import ChecklistWidget
from app.ui.agenda_widget import AgendaWidget
from app.ui.rss_reader_widget import RssReaderWidget
from app.ui.vault_widget import VaultWidget
from app.ui.help_widget import HelpWidget
from app.ui.audio_player_widget import AudioPlayerWidget

class WorkspaceManager(QObject):
    """
    Manages the creation and display of all internal workspace widgets
    within the main QStackedWidget using a lazy loading strategy.
    """
    def __init__(self, stack, conn, services, managers, parent=None):
        super().__init__(parent)
        self.stack = stack
        self.conn = conn
        self.services = services
        self.managers = managers

        # Initialize all widgets to None for lazy loading
        self.search_results_widget = None
        self.welcome_widget = None
        self.notes_widget = None
        self.kanban_widget = None
        self.gantt_chart_widget = None
        self.checklist_widget = None
        self.agenda_widget = None
        self.rss_reader_widget = None
        self.vault_widget = None
        self.help_widget = None
        self.audio_player_widget = None

    # --- Public Methods to Show Widgets (with Lazy Loading) ---

    def show_welcome_page(self):
        if self.welcome_widget is None:
            self.welcome_widget = WelcomeWidget(self.conn)
            self.stack.addWidget(self.welcome_widget)
            # Connect signals for the new widget
            self.welcome_widget.show_kanban_requested.connect(self.show_kanban_tools)
            self.welcome_widget.show_checklist_requested.connect(self.show_checklist_tools)
            self.welcome_widget.show_reminders_requested.connect(self.show_agenda_tools)
            # Check if other widgets that welcome_widget listens to already exist
            if self.kanban_widget:
                self.kanban_widget.kanban_updated.connect(self.welcome_widget.refresh)
            if self.checklist_widget:
                self.checklist_widget.checklist_updated.connect(self.welcome_widget.refresh)
            if self.agenda_widget:
                self.agenda_widget.agenda_updated.connect(self.welcome_widget.refresh)
        self.stack.setCurrentWidget(self.welcome_widget)

    def show_help_manual(self):
        if self.help_widget is None:
            self.help_widget = HelpWidget()
            self.stack.addWidget(self.help_widget)
        self.stack.setCurrentWidget(self.help_widget)

    def show_notes_tools(self):
        if self.notes_widget is None:
            self.notes_widget = NotesWidget(self.services['notes'])
            self.stack.addWidget(self.notes_widget)
            # Connect signals for the new widget
            if self.search_results_widget:
                 self.search_results_widget.result_clicked.connect(self.on_search_result_clicked)
        self.stack.setCurrentWidget(self.notes_widget)

    def show_kanban_tools(self):
        if self.kanban_widget is None:
            self.kanban_widget = KanbanWidget(self.services['kanban'], self.managers['settings'])
            self.stack.addWidget(self.kanban_widget)
            # Connect signals for the new widget
            if self.welcome_widget:
                self.kanban_widget.kanban_updated.connect(self.welcome_widget.refresh)
            if self.checklist_widget:
                self.kanban_widget.kanban_updated.connect(self.checklist_widget.refresh_kanban_cards)
            if self.gantt_chart_widget:
                self.kanban_widget.kanban_updated.connect(self.gantt_chart_widget.refresh_gantt)
            if self.search_results_widget:
                self.search_results_widget.result_clicked.connect(self.on_search_result_clicked)
        self.stack.setCurrentWidget(self.kanban_widget)

    def show_gantt_chart_tools(self):
        if self.gantt_chart_widget is None:
            self.gantt_chart_widget = GanttChartWidget(self.conn, self.managers['settings'])
            self.stack.addWidget(self.gantt_chart_widget)
            # Connect signals for the new widget
            if self.kanban_widget:
                self.kanban_widget.kanban_updated.connect(self.gantt_chart_widget.refresh_gantt)
        self.gantt_chart_widget.refresh_gantt()
        self.stack.setCurrentWidget(self.gantt_chart_widget)

    def show_checklist_tools(self):
        if self.checklist_widget is None:
            self.checklist_widget = ChecklistWidget(self.services['checklist'], self.services['kanban'], self.managers['settings'])
            self.stack.addWidget(self.checklist_widget)
            # Connect signals for the new widget
            if self.welcome_widget:
                self.checklist_widget.checklist_updated.connect(self.welcome_widget.refresh)
            if self.kanban_widget:
                self.kanban_widget.kanban_updated.connect(self.checklist_widget.refresh_kanban_cards)
        self.stack.setCurrentWidget(self.checklist_widget)

    def show_agenda_tools(self):
        if self.agenda_widget is None:
            self.agenda_widget = AgendaWidget(self.services['reminders'])
            self.stack.addWidget(self.agenda_widget)
            # Connect signals for the new widget
            if self.welcome_widget:
                self.agenda_widget.agenda_updated.connect(self.welcome_widget.refresh)
        self.agenda_widget.load_agenda_items()
        self.stack.setCurrentWidget(self.agenda_widget)

    def show_rss_reader_tools(self):
        if self.rss_reader_widget is None:
            self.rss_reader_widget = RssReaderWidget(self.conn)
            self.stack.addWidget(self.rss_reader_widget)
        self.stack.setCurrentWidget(self.rss_reader_widget)

    def show_vault_tools(self):
        if self.vault_widget is None:
            self.vault_widget = VaultWidget(self.managers['vault'])
            self.stack.addWidget(self.vault_widget)
        self.stack.setCurrentWidget(self.vault_widget)

    def show_audio_player_tools(self):
        if self.audio_player_widget is None:
            self.audio_player_widget = AudioPlayerWidget(self.managers['settings'])
            self.stack.addWidget(self.audio_player_widget)
        self.stack.setCurrentWidget(self.audio_player_widget)
        
    def show_search_results(self, results, query):
        if self.search_results_widget is None:
            self.search_results_widget = SearchResultsWidget(self.managers['search'])
            self.stack.addWidget(self.search_results_widget)
            # Connect signals for the new widget
            self.search_results_widget.result_clicked.connect(self.on_search_result_clicked)
        self.search_results_widget.display_results(results, query)
        self.stack.setCurrentWidget(self.search_results_widget)

    def on_search_result_clicked(self, result_data):
        result_type = result_data.get('type')
        result_id = result_data.get('id')
        if result_type == 'note':
            self.show_notes_tools() # This will create the widget if it doesn't exist
            self.notes_widget.find_and_select_note(result_id)
        elif result_type == 'kanban_card':
            self.show_kanban_tools() # This will create the widget if it doesn't exist
            self.kanban_widget.find_and_highlight_card(result_id)