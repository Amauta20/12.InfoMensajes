import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QStandardPaths
from app.ui.main_window import MainWindow
from app.db.database import create_schema
from app.core.di_container import DIContainer
from app.core.error_handler import AppErrorHandler
# import resources_rc

import logging, threading

def setup_qt_environment():
    """
    Configures Qt environment variables for optimal performance and stability.
    
    This function centralizes all Qt-related environment configuration:
    - Disables GPU acceleration to avoid QtWebEngine crashes
    - Disables WebGL for better performance
    - Limits disk cache to reduce I/O overhead
    - Forces software rendering for compatibility
    """
    # GPU and rendering configuration
    flags = [
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-gpu-compositing",
        "--disable-gpu-rasterization",
        "--no-sandbox",
        "--use-angle=swiftshader",
        "--disable-webgl",              # Disable WebGL for performance (Item 8)
        "--disable-webgl2",             # Disable WebGL 2.0
        "--disk-cache-size=0",          # Limit cache to reduce I/O (Item 8)
    ]
    
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(flags)
    os.environ["QT_QUICK_BACKEND"] = "software"
    os.environ["QTWEBENGINE_CHROMIUM_ARGUMENTS"] = "--use-angle=d3d11"
    os.environ["QT_OPENGL"] = "software"
    
    logging.info("Qt environment configured successfully")

# Initialize Qt environment before any Qt imports
setup_qt_environment()

def update_service_scripts(conn):
    """
    Updates the unread_script for existing services in the database
    with the latest scripts from the catalog.json file.
    """
    logging.info("Checking for service script updates...")
    from app.services.service_manager import ServiceManager
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
                logging.info(f"Updating script for '{service_name}'...")
                cursor = conn.cursor()
                cursor.execute("UPDATE services SET unread_script = ? WHERE id = ?", (new_script, service['id']))
                conn.commit()

def main():
    # Initialize Error Handler and Logging first
    error_handler = AppErrorHandler()
    
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

    logging.info(f"Checking for database at: {db_path}")

    # Initialize DI Container
    container = DIContainer.initialize(db_path)
    
    # Ensure the database schema is created on startup
    create_schema(container.conn)

    # Update service scripts from catalog in background thread
    update_thread = threading.Thread(target=update_service_scripts, args=(container.conn,), daemon=True)
    update_thread.start()

    app = QApplication(sys.argv)
    
    # Apply the saved theme (or default to dark)
    try:
        current_theme = container.theme_manager.get_current_theme()
        container.theme_manager.apply_theme(current_theme, app)
    except Exception as e:
        logging.error(f"Failed to apply theme: {e}")
        # Fallback if theme file is missing, though ThemeManager handles defaults


    # --- Show Application Lock Screen ---
    from app.ui.lock_screen import LockScreen
    from PyQt6.QtWidgets import QDialog

    app_security_manager = container.app_security_manager

    if app_security_manager.is_lock_enabled():
        lock_screen = None
        if not app_security_manager.has_lock_password():
            # If lock is enabled but no password is set, force user to set one
            QMessageBox.information(None, "Configuración de Bloqueo", "El bloqueo de la aplicación está activado pero no tienes una contraseña establecida. Por favor, establece una ahora.")
            lock_screen = LockScreen(app_security_manager, is_setting_password=True)
        else:
            # Otherwise, just ask for the password to unlock
            lock_screen = LockScreen(app_security_manager)

        if lock_screen.exec() != QDialog.DialogCode.Accepted:
            container.close()
            sys.exit(0) # User quit or failed to unlock
        
    # --- If unlocked, show main window ---
    window = MainWindow(container) # Pass container instance
    window.show()
    exit_code = app.exec()
    container.close() # Close connection when app exits
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
