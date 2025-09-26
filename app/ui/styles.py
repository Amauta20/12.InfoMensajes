dark_theme_stylesheet = """
QWidget {
    background-color: #222222;
    color: #E0E0E0;
}

QMainWindow {
    background-color: #222222;
}

QToolBar {
    background-color: #333333;
    border: none;
}

QLineEdit, QTextEdit, QListWidget, QDateTimeEdit {
    background-color: #333333;
    color: #E0E0E0;
    border: 1px solid #666666;
    padding: 5px;
    border-radius: 3px;
}

QPushButton {
    background-color: #007ACC; /* A vibrant blue */
    color: #FFFFFF;
    border: 1px solid #005F99;
    padding: 8px 15px;
    border-radius: 5px;
}

QPushButton:hover {
    background-color: #008CDE;
}

QPushButton:pressed {
    background-color: #006BB3;
}

QLabel {
    color: #E0E0E0;
}

QSplitter::handle {
    background-color: #666666;
}

QStackedWidget {
    background-color: #222222;
}

QWebEngineView {
    background-color: #222222;
}

QGroupBox {
    border: 1px solid #444444;
    border-radius: 5px;
    margin-top: 1ex; /* Space for the title */
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center; /* Position at top center */
    padding: 0 3px;
    color: #E0E0E0;
}

QListWidget::item {
    background-color: #2e2e2e;
    border-bottom: 1px solid #444444;
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #005F99; /* Darker blue for selected items */
    color: #FFFFFF;
}
"""

light_theme_stylesheet = """
/* Default (light) theme - essentially empty to use system defaults or minimal styling */
/* QWidget { background-color: #f0f0f0; color: #333; } */
"""
