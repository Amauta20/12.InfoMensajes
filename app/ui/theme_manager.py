"""Theme management for InfoMensajes Power application.

This module provides dynamic theme switching capabilities, allowing users
to toggle between dark and light modes at runtime.
"""
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication


class ThemeManager:
    """Manages application themes and provides dynamic theme switching."""
    
    DARK_THEME = "dark"
    LIGHT_THEME = "light"
    
    def __init__(self, settings_manager):
        """Initialize the ThemeManager.
        
        Args:
            settings_manager: SettingsManager instance for persisting theme preference
        """
        self.settings_manager = settings_manager
        self.themes_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "themes"
        self.current_theme = self._load_saved_theme()
    
    def _load_saved_theme(self) -> str:
        """Load the user's saved theme preference from settings.
        
        Returns:
            Theme name (dark or light), defaults to dark if not set
        """
        return self.settings_manager.get_setting("theme", self.DARK_THEME)
    
    def get_current_theme(self) -> str:
        """Get the currently active theme name.
        
        Returns:
            Current theme name (dark or light)
        """
        return self.current_theme
    
    def load_stylesheet(self, theme_name: str) -> str:
        """Load a stylesheet from a QSS file.
        
        Args:
            theme_name: Name of the theme (dark or light)
            
        Returns:
            Stylesheet content as a string
            
        Raises:
            FileNotFoundError: If the theme file doesn't exist
        """
        theme_file = self.themes_dir / f"{theme_name}.qss"
        
        if not theme_file.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_file}")
        
        with open(theme_file, "r", encoding="utf-8") as f:
            return f.read()
    
    def apply_theme(self, theme_name: str, app: QApplication = None) -> None:
        """Apply a theme to the application.
        
        Args:
            theme_name: Name of the theme to apply (dark or light)
            app: QApplication instance (if None, uses QApplication.instance())
        """
        if app is None:
            app = QApplication.instance()
        
        if app is None:
            raise RuntimeError("No QApplication instance available")
        
        stylesheet = self.load_stylesheet(theme_name)
        app.setStyleSheet(stylesheet)
        
        # Save the theme preference
        self.current_theme = theme_name
        self.settings_manager.set_setting("theme", theme_name)
    
    def toggle_theme(self, app: QApplication = None) -> str:
        """Toggle between dark and light themes.
        
        Args:
            app: QApplication instance (if None, uses QApplication.instance())
            
        Returns:
            The new theme name that was applied
        """
        new_theme = self.LIGHT_THEME if self.current_theme == self.DARK_THEME else self.DARK_THEME
        self.apply_theme(new_theme, app)
        return new_theme
