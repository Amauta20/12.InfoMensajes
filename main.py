import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QStandardPaths
from app.ui.main_window import MainWindow
from app.db.database import create_schema, get_db_connection
from app.search.search_manager import SearchManager
from app.metrics.metrics_manager import MetricsManager
from app.db.settings_manager import SettingsManager
from app.db.notes_manager import NotesManager
from app.db.kanban_manager import KanbanManager
from app.security.vault_manager import VaultManager
from app.services.service_manager import ServiceManager
import datetime
from app.security.vault import Vault
from app.security.app_security_manager import AppSecurityManager
from app.ui.styles import dark_theme_stylesheet

# Workaround for QtWebEngine GPU issues
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --disable-gpu-compositing --disable-gpu-rasterization --no-sandbox"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QTWEBENGINE_CHROMIUM_ARGUMENTS"] = "--use-angle=d3d11"
os.environ["QT_OPENGL"] = "software"

import logging

def update_service_scripts(conn):
    """
    Updates the unread_script for existing services in the database
    with the latest scripts from the catalog.json file.
    """
    print("Checking for service script updates...")
    service_manager = ServiceManager(conn)
    catalog_services = service_manager.load_catalog()
    catalog_scripts = {service['name']: service.get('unread_script') for service in catalog_services}

    db_services = service_manager.get_all_services()
    
    for service in db_services:
        service_name = service['name']
        # Handle cases like "WhatsApp (Work)" matching "WhatsApp"
        base_service_name = service_name.split(' (')[0]
        
        if base_service_name in catalog_scripts:
            new_script = catalog_scripts[base_service_name]
            # Only update if the script is different
            if service['unread_script'] != new_script:
                print(f"Updating script for '{service_name}'...")
                cursor = conn.cursor()
                cursor.execute("UPDATE services SET unread_script = ? WHERE id = ?", (new_script, service['id']))
                conn.commit()

def main():
    # # DEPRECATED: The automatic deletion of 'database.db' has been disabled to prevent data loss.
    # old_db_path = os.path.join(os.getcwd(), "database.db")
    # if os.path.exists(old_db_path):
    #     os.remove(old_db_path)

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Determine database path dynamically
    if getattr(sys, 'frozen', False):
        # Running in a bundled executable (e.g., PyInstaller)
        app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        if not app_data_dir:
            # Fallback if AppDataLocation is not available (shouldn't happen on Windows)
            app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "InfoMensajesApp")
        db_dir = os.path.join(app_data_dir, "db")
        os.makedirs(db_dir, exist_ok=True) # Ensure directory exists
        db_path = os.path.join(db_dir, "infomensajes.db")
    else:
        # Running in development mode
        db_path = os.path.join(os.getcwd(), "x", "database.db") # Use the project root for dev DB

    print(f"Checking for database at: {db_path}")

    # Create a single connection here
    conn = get_db_connection(db_path)

    # Ensure the database schema is created on startup
    create_schema(conn)

    # Update service scripts from catalog
    update_service_scripts(conn)

    # Initialize SettingsManager singleton
    SettingsManager.initialize(conn)

    # Initialize metrics manager after schema is created
    global_metrics_manager = MetricsManager.get_instance(conn)

    # Instantiate SearchManager
    search_manager_instance = SearchManager(conn)
    # FTS indexes are now updated automatically by database triggers, so manual rebuild is removed.

    # Instantiate VaultManager
    vault_manager_instance = VaultManager(conn)

    # Initialize AIManager
    from app.ai.ai_manager import AIManager
    AIManager.initialize(SettingsManager.get_instance(), vault_manager_instance)

    # Initialize AppSecurityManager
    app_security_manager = AppSecurityManager(SettingsManager.get_instance())

    app = QApplication(sys.argv)
    app.setStyleSheet(dark_theme_stylesheet)

    # --- Show Application Lock Screen ---
    from app.ui.lock_screen import LockScreen
    from PyQt6.QtWidgets import QDialog

    if app_security_manager.is_lock_enabled():
        lock_screen = None
        if not app_security_manager.has_lock_password():
            # If lock is enabled but no password is set, force user to set one
            QMessageBox.information(lock_screen, "Configuración de Bloqueo", "El bloqueo de la aplicación está activado pero no tienes una contraseña establecida. Por favor, establece una ahora.")
            lock_screen = LockScreen(app_security_manager, is_setting_password=True)
        else:
            # Otherwise, just ask for the password to unlock
            lock_screen = LockScreen(app_security_manager)

        if lock_screen.exec() != QDialog.DialogCode.Accepted:
            conn.close()
            sys.exit(0) # User quit or failed to unlock
        
    # --- If unlocked, show main window ---
    window = MainWindow(conn, global_metrics_manager, vault_manager_instance) # Pass instances
    window.show()
    exit_code = app.exec()
    conn.close() # Close connection when app exits
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
