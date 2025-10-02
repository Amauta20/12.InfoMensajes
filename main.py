import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.db.database import create_schema
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

    db_path = os.path.join(os.getcwd(), "infomensajero.db")
    print(f"Checking for database at: {db_path}")
    if os.path.exists(db_path):
        print("Database file found.")
    else:
        print("Database file NOT found.")
    


    app = QApplication(sys.argv)
    app.setStyleSheet(dark_theme_stylesheet)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
