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
"""

light_theme_stylesheet = """
/* Default (light) theme - essentially empty to use system defaults or minimal styling */
/* QWidget { background-color: #f0f0f0; color: #333; } */
"""
