import os
from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices, QAction
from PyQt6.QtWidgets import QMenu, QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView

class LinkHandlingPage(QWebEnginePage):
    """
    Custom QWebEnginePage to handle navigation requests.
    Opens external links in the default system browser.
    """
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if _type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked and isMainFrame:
            # Allow navigation to common login domains within the app
            allowed_hosts = [
                "login.microsoftonline.com", "login.live.com", "teams.microsoft.com",
                "www.messenger.com", "www.facebook.com", "accounts.google.com"
            ]
            if url.host() in allowed_hosts:
                return True
            # If the link is to a different domain, open it externally
            if self.url().host() and url.host() != self.url().host():
                QDesktopServices.openUrl(url)
                return False
        return True

class CustomWebEngineView(QWebEngineView):
    """
    Custom QWebEngineView with a rich context menu.
    """
    def contextMenuEvent(self, event):
        pos = event.globalPos()
        js_script = f"""
            (function() {{
                try {{
                    let element = document.elementFromPoint({event.pos().x()}, {event.pos().y()});
                    if (!element) return null;
                    let isContentEditable = element.isContentEditable;
                    let linkUrl = element.closest('a') ? element.closest('a').href : '';
                    let imageUrl = element.tagName === 'IMG' ? element.src : '';
                    let hasSelection = !window.getSelection().isCollapsed;
                    return {{
                        'isContentEditable': isContentEditable, 'linkUrl': linkUrl,
                        'imageUrl': imageUrl, 'hasSelection': hasSelection
                    }};
                }} catch (e) {{
                    console.error("Error in context menu script: " + e);
                    return null;
                }}
            }})();
        """
        import weakref
        weak_self = weakref.ref(self)
        def safe_context_menu_callback(result):
            strong_self = weak_self()
            if strong_self:
                strong_self._build_context_menu(result, pos)
        self.page().runJavaScript(js_script, safe_context_menu_callback)

    def _build_context_menu(self, data, pos):
        if not data: return
        menu = QMenu(self)
        if data.get('imageUrl'):
            menu.addAction("Copiar imagen", lambda: self.page().triggerAction(QWebEnginePage.WebAction.CopyImage))
            menu.addAction("Guardar imagen como...", lambda: self.page().triggerAction(QWebEnginePage.WebAction.DownloadImageToDisk))
            menu.addSeparator()
        if data.get('linkUrl'):
            link_url = QUrl(data['linkUrl'])
            menu.addAction("Abrir enlace en navegador externo", lambda: QDesktopServices.openUrl(link_url))
            menu.addAction("Copiar dirección de enlace", lambda: QApplication.clipboard().setText(link_url.toString()))
            menu.addSeparator()
        if data.get('hasSelection'):
            menu.addAction("Copiar", lambda: self.page().triggerAction(QWebEnginePage.WebAction.Copy))
        if data.get('isContentEditable'):
            if not data.get('hasSelection'):
                menu.addAction("Copiar", lambda: self.page().triggerAction(QWebEnginePage.WebAction.Copy))
            menu.addAction("Cortar", lambda: self.page().triggerAction(QWebEnginePage.WebAction.Cut))
            menu.addAction("Pegar", lambda: self.page().triggerAction(QWebEnginePage.WebAction.Paste))
            menu.addSeparator()
            menu.addAction("Deshacer", lambda: self.page().triggerAction(QWebEnginePage.WebAction.Undo))
            menu.addAction("Rehacer", lambda: self.page().triggerAction(QWebEnginePage.WebAction.Redo))
            menu.addSeparator()
            menu.addAction("Seleccionar todo", lambda: self.page().triggerAction(QWebEnginePage.WebAction.SelectAll))
        if menu.actions():
            menu.addSeparator()
        
        action_back = menu.addAction("Atrás")
        action_back.triggered.connect(self.back)
        action_back.setEnabled(self.page().history().canGoBack())
        action_forward = menu.addAction("Adelante")
        action_forward.triggered.connect(self.forward)
        action_forward.setEnabled(self.page().history().canGoForward())
        menu.addAction("Recargar", self.reload)
        if not menu.isEmpty():
            menu.exec(pos)

class WebViewManager(QObject):
    """Manages the creation, loading, and lifecycle of service web views."""
    unread_status_changed = pyqtSignal(int, bool)
    notification_requested = pyqtSignal(str, str)

    def __init__(self, web_view_stack, service_manager, parent=None):
        super().__init__(parent)
        self.web_view_stack = web_view_stack
        self.service_manager = service_manager
        self.web_views = {}

        # Timer to periodically check for unread messages
        self.unread_check_timer = QTimer(self)
        self.unread_check_timer.timeout.connect(self.run_unread_check_on_current_view)
        self.unread_check_timer.start(5000) # Check every 5 seconds

    def run_unread_check_on_current_view(self):
        """
        Checks the unread status of the currently active web view if it's a service.
        """
        current_view = self.web_view_stack.currentWidget()
        # Check if the widget is a CustomWebEngineView and has a service_id
        if isinstance(current_view, CustomWebEngineView) and current_view.property('service_id'):
            service_id = current_view.property('service_id')
            self._check_unread_messages_for_service(service_id, current_view)

    def load_service(self, url, profile_path):
        service_details = self.service_manager.get_service_by_profile_path(profile_path)
        if not service_details:
            print(f"Error: Service details not found for profile_path: {profile_path}")
            return

        if profile_path in self.web_views:
            view = self.web_views[profile_path]
        else:
            profile_name = os.path.basename(profile_path)
            profile = QWebEngineProfile(profile_name, self)
            profile.setPersistentStoragePath(profile_path)
            profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            profile.downloadRequested.connect(self._handle_download_requested)

            view = CustomWebEngineView()
            page = LinkHandlingPage(profile, view)
            page.featurePermissionRequested.connect(self.handle_permission_request)
            view.setPage(page)
            view.setProperty('service_id', service_details['id'])
            view.loadFinished.connect(self._on_web_view_load_finished)
            view.setUrl(QUrl(url))
            
            self.web_views[profile_path] = view
            self.web_view_stack.addWidget(view)

        self.web_view_stack.setCurrentWidget(view)

    def remove_webview_for_service(self, service_id):
        service_details = self.service_manager.get_service_by_id(service_id)
        if not service_details: return

        profile_path = service_details['profile_path']
        if profile_path in self.web_views:
            view_to_remove = self.web_views.pop(profile_path)
            self.web_view_stack.removeWidget(view_to_remove)
            view_to_remove.deleteLater()

    def _on_web_view_load_finished(self, ok):
        view = self.sender()
        if not ok:
            print(f"Page failed to load: {view.url().toString()}")
            return

        js_script_links = """
            document.querySelectorAll('a').forEach(function(link) {
                if (link.hostname && link.hostname !== window.location.hostname) {
                    link.setAttribute('title', 'Este enlace se abrirá en un navegador externo');
                    link.style.cursor = 'alias';
                }
            });
        """
        view.page().runJavaScript(js_script_links)

        service_id = view.property('service_id')
        if service_id:
            self._check_unread_messages_for_service(service_id, view)

    def _check_unread_messages_for_service(self, service_id, view):
        service_details = self.service_manager.get_service_by_id(service_id)
        if not service_details: return

        js_script = service_details['unread_script']
        if js_script:
            import weakref
            weak_self = weakref.ref(self)
            def safe_unread_callback(result):
                strong_self = weak_self()
                if strong_self:
                    strong_self._handle_unread_result(service_id, result)
            view.page().runJavaScript(js_script, safe_unread_callback)
        else:
            self._handle_unread_result(service_id, False)

    def _handle_unread_result(self, service_id, has_unread):
        print(f"[DEBUG] Unread status for service {service_id}: {has_unread}")
        self.unread_status_changed.emit(service_id, bool(has_unread))

    def _handle_download_requested(self, download):
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)
        
        file_name = download.downloadFileName() or os.path.basename(download.url().path())
        download.setDownloadDirectory(downloads_path)
        if file_name:
            download.setDownloadFileName(file_name)
            
        download.accept()
        self.notification_requested.emit("Descarga Aceptada", f"El archivo se está descargando en {downloads_path}")

    def handle_permission_request(self, securityOrigin, feature):
        if feature == QWebEnginePage.Feature.ClipboardReadWrite:
            page = self.sender()
            page.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)