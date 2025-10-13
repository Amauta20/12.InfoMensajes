dark_theme_stylesheet = """
QWidget {
    background-color: #2e2e2e;
    color: #f0f0f0;
}

QMainWindow {
    background-color: #2e2e2e;
}

QToolBar {
    background-color: #3a3a3a;
    border: none;
}

QLineEdit, QTextEdit, QListWidget {
    background-color: #3a3a3a;
    color: #f0f0f0;
    border: 1px solid #555;
    padding: 5px;
}

QPushButton {
    background-color: #555;
    color: #f0f0f0;
    border: 1px solid #666;
    padding: 5px 10px;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #666;
}

QPushButton:pressed {
    background-color: #444;
}

QPushButton.unread {
    background-color: #e74c3c; /* A shade of red/orange */
    font-weight: bold;
}

QPushButton.unread:hover {
    background-color: #c0392b;
}

QLabel {
    color: #f0f0f0;
}

QSplitter::handle {
    background-color: #555;
}

QStackedWidget {
    background-color: #2e2e2e;
}

QWebEngineView {
    background-color: #2e2e2e;
}

QTabWidget::pane { /* The tab widget frame */
    border-top: 2px solid #444;
    background-color: #3a3a3a;
}

QTabWidget::tab-bar {
    left: 5px; /* move to the right by 5px */
}

QTabBar::tab {
    background: #555;
    border: 1px solid #777;
    border-bottom-color: #555; /* same as pane color */
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 8ex;
    padding: 5px 10px;
    color: #f0f0f0;
}

QTabBar::tab:selected, QTabBar::tab:hover {
    background: #666;
}

QTabBar::tab:selected {
    border-color: #777;
    border-bottom-color: #666; /* same as selected tab color */
}

QTabBar::tab:!selected {
    margin-top: 2px; /* make non-selected tabs look smaller */
}
"""

light_theme_stylesheet = """
/* Default (light) theme - essentially empty to use system defaults or minimal styling */
/* QWidget { background-color: #f0f0f0; color: #333; } */
"""
