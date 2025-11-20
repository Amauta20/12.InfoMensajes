"""Centralized error handling and logging configuration for InfoMensajes Power.

This module provides the AppErrorHandler class to catch uncaught exceptions,
log them to a file with rotation, and display a user-friendly error dialog
before the application exits.
"""
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QApplication

class AppErrorHandler:
    """Handles uncaught exceptions and configures application logging."""

    def __init__(self, app_name="InfoMensajesApp", log_dir=None):
        """Initialize the error handler.

        Args:
            app_name: Name of the application (used for log filename).
            log_dir: Directory to store log files. If None, uses default location.
        """
        self.app_name = app_name
        self.log_dir = log_dir or self._get_default_log_dir()
        self._setup_logging()
        
        # Install exception hook
        sys.excepthook = self.handle_exception

    def _get_default_log_dir(self) -> Path:
        """Get the default directory for log files."""
        if getattr(sys, 'frozen', False):
            # Prod: AppData/Local/InfoMensajesApp/logs
            base_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
            log_dir = base_dir / self.app_name / "logs"
        else:
            # Dev: project_root/logs
            log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _setup_logging(self):
        """Configure logging with rotating file handler."""
        log_file = self.log_dir / f"{self.app_name.lower()}.log"
        
        # Create handlers
        # 1. Rotating File Handler (1MB size, keep last 5 backups)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # 2. Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        logging.info(f"Logging initialized. Log file: {log_file}")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Global exception handler to log errors and show dialog."""
        # Ignore KeyboardInterrupt so Ctrl+C works
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.critical("Uncaught exception:\n%s", error_msg)

        # Show error dialog if UI is available
        app = QApplication.instance()
        if app:
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setWindowTitle("Error Inesperado")
            error_box.setText(f"Ha ocurrido un error inesperado en {self.app_name}.")
            error_box.setInformativeText("La aplicación necesita cerrarse. Los detalles han sido registrados.")
            error_box.setDetailedText(error_msg)
            error_box.exec()
        
        # Call default excepthook (prints to stderr)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        sys.exit(1)
