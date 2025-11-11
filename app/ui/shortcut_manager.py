from PyQt6.QtCore import QObject
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWebEngineCore import QWebEnginePage

class ShortcutManager(QObject):
    """Manages all global keyboard shortcuts for the application."""
    def __init__(self, parent, search_input, web_view_stack):
        super().__init__(parent)
        self.search_input = search_input
        self.web_view_stack = web_view_stack

        self._create_shortcuts()

    def _create_shortcuts(self):
        """Creates and connects all the QShortcut objects."""
        # Global Search Shortcut
        QShortcut(QKeySequence("Ctrl+F"), self.parent()).activated.connect(self.focus_search_bar)
        
        # Web Actions
        QShortcut(QKeySequence("F5"), self.parent()).activated.connect(self.reload_current_page)
        QShortcut(QKeySequence("Ctrl+C"), self.parent()).activated.connect(self.copy_selection)
        QShortcut(QKeySequence("Ctrl+V"), self.parent()).activated.connect(self.paste_from_clipboard)
        QShortcut(QKeySequence("Ctrl+X"), self.parent()).activated.connect(self.cut_selection)
        QShortcut(QKeySequence("Ctrl+A"), self.parent()).activated.connect(self.select_all_content)
        QShortcut(QKeySequence("Ctrl+Z"), self.parent()).activated.connect(self.undo_action)
        QShortcut(QKeySequence("Ctrl+Y"), self.parent()).activated.connect(self.redo_action)

    def focus_search_bar(self):
        """Focuses the global search input bar."""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _get_current_webview(self):
        """
        Finds and returns the currently active QWebEngineView instance,
        whether it's a direct service view or embedded in another widget.
        """
        # Local import to prevent potential circular dependencies
        from app.ui.webview_manager import CustomWebEngineView
        
        current_widget = self.web_view_stack.currentWidget()
        if isinstance(current_widget, CustomWebEngineView):
            return current_widget
        if hasattr(current_widget, 'web_view'): # For widgets that contain a webview
            return current_widget.web_view
        return None

    # --- Slots for Web Action Shortcuts ---

    def reload_current_page(self):
        webview = self._get_current_webview()
        if webview: webview.reload()

    def copy_selection(self):
        webview = self._get_current_webview()
        if webview: webview.page().triggerAction(QWebEnginePage.WebAction.Copy)

    def paste_from_clipboard(self):
        webview = self._get_current_webview()
        if webview: webview.page().triggerAction(QWebEnginePage.WebAction.Paste)

    def cut_selection(self):
        webview = self._get_current_webview()
        if webview: webview.page().triggerAction(QWebEnginePage.WebAction.Cut)

    def select_all_content(self):
        webview = self._get_current_webview()
        if webview: webview.page().triggerAction(QWebEnginePage.WebAction.SelectAll)

    def undo_action(self):
        webview = self._get_current_webview()
        if webview: webview.page().triggerAction(QWebEnginePage.WebAction.Undo)

    def redo_action(self):
        webview = self._get_current_webview()
        if webview: webview.page().triggerAction(QWebEnginePage.WebAction.Redo)
