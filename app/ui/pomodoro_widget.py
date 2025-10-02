from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtCore import QTimer, QTime, pyqtSignal as Signal
from app.db import settings_manager

class PomodoroWidget(QWidget):
    pomodoro_finished = Signal(str)

    def __init__(self):
        super().__init__()
        self.load_settings()

        self.current_mode = "Pomodoro"
        self.time_left = QTime(0, self.modes[self.current_mode], 0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.layout = QHBoxLayout(self)

        self.time_label = QLabel(self.time_left.toString("mm:ss"))
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.time_label)

        self.start_button = QPushButton("Iniciar")
        self.start_button.clicked.connect(self.start_timer)
        self.layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setVisible(False)
        self.layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("Reiniciar")
        self.reset_button.clicked.connect(self.reset_timer)
        self.layout.addWidget(self.reset_button)

        self.mode_buttons_layout = QHBoxLayout()
        for mode in ["Pomodoro", "Descanso Corto", "Descanso Largo"]:
            button = QPushButton(mode)
            button.setCheckable(True)
            if mode == self.current_mode:
                button.setChecked(True)
            button.clicked.connect(lambda checked, m=mode: self.switch_mode(m))
            self.mode_buttons_layout.addWidget(button)
        self.layout.addLayout(self.mode_buttons_layout)

    def load_settings(self):
        self.modes = {
            "Pomodoro": settings_manager.get_pomodoro_duration(),
            "Descanso Corto": settings_manager.get_short_break_duration(),
            "Descanso Largo": settings_manager.get_long_break_duration(),
        }

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