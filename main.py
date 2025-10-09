import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.db.database import create_schema
from app.search.search_manager import rebuild_fts_indexes
from app.metrics.metrics_manager import MetricsManager
from app.db import notes_manager, kanban_manager
import datetime
from app.security.vault import Vault
from app.ui.styles import dark_theme_stylesheet

# Workaround for QtWebEngine GPU issues
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --disable-gpu-compositing --disable-gpu-rasterization --no-sandbox"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QTWEBENGINE_CHROMIUM_ARGUMENTS"] = "--use-angle=d3d11"
os.environ["QT_OPENGL"] = "software"

def main():
    # Ensure the database schema is created on startup
    create_schema()
    rebuild_fts_indexes()

    # Initialize metrics manager after schema is created
    global_metrics_manager = MetricsManager.get_instance()

    db_path = os.path.join(os.getcwd(), "infomensajero.db")
    print(f"Checking for database at: {db_path}")
    if os.path.exists(db_path):
        print("Database file found.")
    else:
        print("Database file NOT found.")
    

    app = QApplication(sys.argv)
    app.setStyleSheet(dark_theme_stylesheet)
    window = MainWindow(global_metrics_manager)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
