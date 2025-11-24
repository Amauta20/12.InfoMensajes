from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QFontDatabase
from PyQt6.QtCore import Qt
import os

class IconManager:
    """
    Manages Font Awesome icons generation.
    """
    
    # Font Awesome 5 Free Solid Unicode mapping
    ICONS = {
        "search": "\uf002",
        "clock": "\uf017",
        "chart-bar": "\uf080",
        "robot": "\uf544",
        "adjust": "\uf042",
        "cog": "\uf013",
        "question-circle": "\uf059",
        "sticky-note": "\uf249",
        "columns": "\uf0db",
        "stream": "\uf550",
        "check-square": "\uf14a",
        "bell": "\uf0f3",
        "rss": "\uf09e",
        "key": "\uf084",
        "music": "\uf001",
        "plus": "\uf067",
        "globe": "\uf0ac",
        "edit": "\uf044",
        "trash": "\uf1f8",
        "copy": "\uf0c5",
        "play": "\uf04b",
        "pause": "\uf04c",
        "redo": "\uf01e",
        "eye": "\uf06e",
        "eye-slash": "\uf070",
        "save": "\uf0c7",
        "times": "\uf00d",
        "palette": "\uf53f",
        "lock": "\uf023",
        "unlock": "\uf09c",
        "magic": "\uf0d0",
        "list-ul": "\uf0ca",
        "file-alt": "\uf15c",
        "gavel": "\uf0e3",
        "check": "\uf00c",
        "cogs": "\uf085",
        "tasks": "\uf0ae",
        "list": "\uf03a",
        "search": "\uf002",
        "share-alt": "\uf1e0",
        "users": "\uf0c0",
        "envelope": "\uf0e0",
        "globe": "\uf0ac",
        "paper-plane": "\uf1d8",
        "hashtag": "\uf292",
        "briefcase": "\uf0b1",
        "headset": "\uf590",
        "camera": "\uf030",
        "comment-dots": "\uf4ad",
        "comment-alt": "\uf27a",
        "envelope-open": "\uf2b6",
        # Service mappings (using generic icons)
        "whatsapp": "\uf4ad", # comment-dots
        "telegram": "\uf1d8", # paper-plane
        "slack": "\uf292", # hashtag
        "gmail": "\uf0e0", # envelope
        "outlook": "\uf2b6", # envelope-open
        "linkedin": "\uf0b1", # briefcase
        "teams": "\uf0c0", # users
        "discord": "\uf590", # headset
        "messenger": "\uf27a", # comment-alt
        "x (twitter)": "\uf292", # hashtag
        "twitter": "\uf292", # hashtag
        "instagram": "\uf030" # camera
    }

    def __init__(self):
        self.font_family = "Font Awesome 5 Free"
        self._load_font()

    def _load_font(self):
        # Try to load from assets
        font_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'fa-solid-900.ttf')
        if not os.path.exists(font_path):
             font_path = os.path.join(os.getcwd(), 'assets', 'fa-solid-900.ttf')
        
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            print(f"IconManager: Failed to load font from {font_path}")

    def get_icon(self, name, color="#f0f0f0", size=32):
        """
        Generates a QIcon from a Font Awesome character.
        """
        if name not in self.ICONS:
            print(f"IconManager: Icon '{name}' not found.")
            return QIcon()

        char = self.ICONS[name]
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        font = QFont(self.font_family)
        font.setPixelSize(int(size * 0.8)) # Adjust size to fit
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        
        painter.setFont(font)
        painter.setPen(QColor(color))
        
        # Center the text
        rect = pixmap.rect()
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, char)
        painter.end()

        return QIcon(pixmap)
