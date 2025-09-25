from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QStackedWidget, QToolBar, QLineEdit, QApplication, QDialog
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
import os

from app.ui.sidebar import Sidebar
from app.search import search_manager
from app.ui.search_results_widget import SearchResultsWidget
from app.ui.styles import dark_theme_stylesheet, light_theme_stylesheet
from app.services import service_manager
from app.ui.welcome_widget import WelcomeWidget
from app.ui.add_service_dialog import AddServiceDialog # Needed for opening dialog from welcome widget
from app.ui.productivity_widget import ProductivityWidget
from app.ui.select_service_dialog import SelectServiceDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("InfoMensajero")
        self.setGeometry(100, 100, 1280, 720)

        self.is_dark_theme = True # Initial state



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

        # Global Search Shortcut (Ctrl+F)
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.focus_search_bar)

        # Theme Toggle Button
        self.theme_toggle_button = self.toolbar.addAction("Cambiar Tema")
        self.theme_toggle_button.triggered.connect(self.toggle_theme)

        # --- Web view management ---
        self.web_view_stack = QStackedWidget()
        self.web_views = {} # Cache for web views: {profile_path: QWebEngineView}

        # Search Results Widget
        self.search_results_widget = SearchResultsWidget()
        self.web_view_stack.addWidget(self.search_results_widget) # Add it to the stack, but not visible initially

        # Welcome Widget
        self.welcome_widget = WelcomeWidget()
        self.welcome_widget.add_service_requested.connect(self.open_add_service_dialog_from_welcome)
        self.web_view_stack.addWidget(self.welcome_widget)

        # Productivity Widget
        self.productivity_widget = ProductivityWidget()
        self.web_view_stack.addWidget(self.productivity_widget)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(240)
        self.sidebar.show_productivity_requested.connect(self.show_productivity_tools)

        # Splitter to manage sidebar and web_view_stack
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.web_view_stack)

        self.main_layout.addWidget(self.splitter)
        self.setCentralWidget(self.central_widget)

        # Connect signals
        self.sidebar.service_selected.connect(self.load_service)
        self.sidebar.service_deleted.connect(self.remove_webview_for_service)

        # Load initial service or a default page
        self.load_initial_page()

    def show_productivity_tools(self):
        self.web_view_stack.setCurrentWidget(self.productivity_widget)

    def trigger_add_service_dialog(self):
        self.sidebar.open_select_service_dialog()

    def open_add_service_dialog_from_welcome(self):
        # This method will be called when the welcome widget requests to add a service
        dialog = SelectServiceDialog(self)
        dialog.catalog_service_selected.connect(self._add_catalog_service_from_welcome)
        dialog.custom_service_requested.connect(self._add_custom_service_from_welcome)
        dialog.exec()

    def _add_catalog_service_from_welcome(self, name, url, icon):
        service_manager.add_service(name, url, icon)
        self.sidebar.load_services() # Refresh the service list in sidebar
        self.load_initial_page() # Try to load the newly added service

    def _add_custom_service_from_welcome(self):
        dialog = AddServiceDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, url, icon = dialog.get_service_data()
            if name and url:
                service_manager.add_service(name, url, icon)
                self.sidebar.load_services() # Refresh the service list in sidebar
                self.load_initial_page() # Try to load the newly added service

    def toggle_theme(self):
        if self.is_dark_theme:
            QApplication.instance().setStyleSheet(light_theme_stylesheet)
            self.is_dark_theme = False
            self.theme_toggle_button.setText("Tema Oscuro")
        else:
            QApplication.instance().setStyleSheet(dark_theme_stylesheet)
            self.is_dark_theme = True
            self.theme_toggle_button.setText("Tema Claro")

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
