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
from app.security.vault_manager import vault_manager
import datetime
from app.security.vault import Vault
from app.ui.styles import dark_theme_stylesheet

# Workaround for QtWebEngine GPU issues
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --disable-gpu-compositing --disable-gpu-rasterization --no-sandbox"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QTWEBENGINE_CHROMIUM_ARGUMENTS"] = "--use-angle=d3d11"
os.environ["QT_OPENGL"] = "software"

def main():
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
        db_path = os.path.join(os.getcwd(), "database.db") # Use the project root for dev DB

    print(f"Checking for database at: {db_path}")

    # Create a single connection here
    conn = get_db_connection(db_path)

    # Initialize SettingsManager singleton
    SettingsManager.initialize(conn)

    # Initialize metrics manager after schema is created
    global_metrics_manager = MetricsManager.get_instance(conn)

    # Ensure the database schema is created on startup
    if not os.path.exists(db_path):
        print("Database file NOT found. Creating new schema.")
        create_schema(conn) # Pass conn
    else:
        # If DB exists, ensure schema is up-to-date (create_schema handles IF NOT EXISTS)
        create_schema(conn)

    # Instantiate SearchManager
    search_manager_instance = SearchManager(conn)
    search_manager_instance.rebuild_fts_indexes() # Rebuild FTS indexes after schema is ensured

    # Set connection for vault_manager
    vault_manager.set_conn(conn) # This will require refactoring vault_manager

    app = QApplication(sys.argv)
    app.setStyleSheet(dark_theme_stylesheet)
    window = MainWindow(conn, global_metrics_manager) # Pass conn
    window.show()
    exit_code = app.exec()
    conn.close() # Close connection when app exits
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
