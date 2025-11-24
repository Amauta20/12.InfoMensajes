from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtCore import QTimer, QTime, pyqtSignal as Signal
from app.db.settings_manager import SettingsManager
from app.ui.icon_manager import IconManager

class PomodoroWidget(QWidget):
    pomodoro_finished = Signal(str)
    focus_mode_toggled = Signal(bool)

    def __init__(self, settings_manager_instance, notification_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager_instance
        self.notification_manager = notification_manager # Store instance
        self.icon_manager = IconManager()
        self.load_settings()

        self.current_mode = "Pomodoro"
        self.time_left = QTime(0, self.modes[self.current_mode], 0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # Compact layout
        self.layout.setSpacing(5)

        self.time_label = QLabel(self.time_left.toString("mm:ss"))
        self.time_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-right: 5px; color: #f0f0f0;")
        self.layout.addWidget(self.time_label)

        self.start_button = QPushButton()
        self.start_button.setToolTip("Iniciar")
        self.start_button.setIcon(self.icon_manager.get_icon("play", size=14))
        self.start_button.clicked.connect(self.start_timer)
        self.layout.addWidget(self.start_button)

        self.pause_button = QPushButton()
        self.pause_button.setToolTip("Pausar")
        self.pause_button.setIcon(self.icon_manager.get_icon("pause", size=14))
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setVisible(False)
        self.layout.addWidget(self.pause_button)

        self.reset_button = QPushButton()
        self.reset_button.setToolTip("Reiniciar")
        self.reset_button.setIcon(self.icon_manager.get_icon("redo", size=14))
        self.reset_button.clicked.connect(self.reset_timer)
        self.layout.addWidget(self.reset_button)

        # Focus Mode Toggle
        self.focus_button = QPushButton("Modo Enfoque")
        self.focus_button.setCheckable(True)
        self.focus_button.setIcon(self.icon_manager.get_icon("eye", size=14))
        self.focus_button.setStyleSheet("""
            QPushButton:checked {
                background-color: #8e44ad;
                border: 1px solid #9b59b6;
            }
            QPushButton {
                padding: 3px 8px;
                font-size: 12px;
            }
        """)
        self.focus_button.toggled.connect(self.toggle_focus_mode)
        self.layout.addWidget(self.focus_button)

        # Mode Buttons
        self.mode_buttons_layout = QHBoxLayout()
        self.mode_buttons_layout.setSpacing(2)
        for mode in ["Pomodoro", "Descanso Corto", "Descanso Largo"]:
            button = QPushButton(mode)
            button.setCheckable(True)
            button.setStyleSheet("""
                QPushButton {
                    padding: 3px 8px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #555;
                }
            """)
            if mode == self.current_mode:
                button.setChecked(True)
            button.clicked.connect(lambda checked, m=mode: self.switch_mode(m))
            self.mode_buttons_layout.addWidget(button)
        self.layout.addLayout(self.mode_buttons_layout)

        # Apply general button style
        for btn in [self.start_button, self.pause_button, self.reset_button]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 3px 8px;
                    font-size: 12px;
                }
            """)

    def load_settings(self):
        self.modes = {
            "Pomodoro": self.settings_manager.get_pomodoro_duration(),
            "Descanso Corto": self.settings_manager.get_short_break_duration(),
            "Descanso Largo": self.settings_manager.get_long_break_duration(),
        }

    def toggle_focus_mode(self, checked):
        self.focus_mode_toggled.emit(checked)
        if checked:
            self.focus_button.setText("Salir de Enfoque")
            self.focus_button.setIcon(self.icon_manager.get_icon("eye-slash", size=14))
        else:
            self.focus_button.setText("Modo Enfoque")
            self.focus_button.setIcon(self.icon_manager.get_icon("eye", size=14))

    def start_timer(self):
        self.timer.start(1000)
        self.start_button.setVisible(False)
        self.pause_button.setVisible(True)

    def pause_timer(self):
        self.timer.stop()
        self.start_button.setVisible(True)
        self.pause_button.setVisible(False)

    def reset_timer(self):
        self.timer.stop()
        self.time_left = QTime(0, self.modes[self.current_mode], 0)
        self.time_label.setText(self.time_left.toString("mm:ss"))
        self.start_button.setVisible(True)
        self.pause_button.setVisible(False)

    def update_timer(self):
        self.time_left = self.time_left.addSecs(-1)
        self.time_label.setText(self.time_left.toString("mm:ss"))
        if self.time_left == QTime(0, 0, 0):
            self.timer.stop()
            self.notification_manager.show_pomodoro_notification(self.current_mode)
            self.pomodoro_finished.emit(self.current_mode)
            self.start_button.setVisible(True)
            self.pause_button.setVisible(False)

    def switch_mode(self, mode):
        self.current_mode = mode
        self.reset_timer()
        for i in range(self.mode_buttons_layout.count()):
            button = self.mode_buttons_layout.itemAt(i).widget()
            if button.text() == mode:
                button.setChecked(True)
            else:
                button.setChecked(False)