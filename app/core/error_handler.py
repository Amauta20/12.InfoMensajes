"""Centralized error handling and logging configuration for InfoMensajes Power.

This module provides the AppErrorHandler class to catch uncaught exceptions,
log them to a file with rotation, and display a user-friendly error dialog
before the application exits.
"""
import sys
import os
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

    # --- Helper Methods for Common Error Scenarios ---

    @staticmethod
    def log_error(message: str, exception: Exception = None):
        """Log an error message with optional exception details.
        
        Args:
            message: Error message to log
            exception: Optional exception object to include in log
        """
        if exception:
            logging.error(f"{message}: {str(exception)}", exc_info=True)
        else:
            logging.error(message)

    @staticmethod
    def log_warning(message: str):
        """Log a warning message.
        
        Args:
            message: Warning message to log
        """
        logging.warning(message)

    @staticmethod
    def log_info(message: str):
        """Log an informational message.
        
        Args:
            message: Info message to log
        """
        logging.info(message)

    @staticmethod
    def log_debug(message: str):
        """Log a debug message.
        
        Args:
            message: Debug message to log
        """
        logging.debug(message)

    @staticmethod
    def show_error_dialog(title: str, message: str, details: str = None):
        """Show an error dialog to the user without exiting the application.
        
        Args:
            title: Dialog window title
            message: Main error message
            details: Optional detailed error information
        """
        app = QApplication.instance()
        if app:
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setWindowTitle(title)
            error_box.setText(message)
            if details:
                error_box.setDetailedText(details)
            error_box.exec()

    @staticmethod
    def show_warning_dialog(title: str, message: str):
        """Show a warning dialog to the user.
        
        Args:
            title: Dialog window title
            message: Warning message
        """
        app = QApplication.instance()
        if app:
            warning_box = QMessageBox()
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setWindowTitle(title)
            warning_box.setText(message)
            warning_box.exec()

    @staticmethod
    def show_info_dialog(title: str, message: str):
        """Show an informational dialog to the user.
        
        Args:
            title: Dialog window title
            message: Information message
        """
        app = QApplication.instance()
        if app:
            info_box = QMessageBox()
            info_box.setIcon(QMessageBox.Icon.Information)
            info_box.setWindowTitle(title)
            info_box.setText(message)
            info_box.exec()
