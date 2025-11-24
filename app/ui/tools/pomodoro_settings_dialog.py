from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDialogButtonBox, QPushButton
from app.db import settings_manager

class PomodoroSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Pomodoro")
        self.layout = QVBoxLayout(self)

        # Pomodoro duration
        self.pomodoro_layout = QHBoxLayout()
        self.pomodoro_label = QLabel("Pomodoro (minutos):")
        self.pomodoro_spinbox = QSpinBox()
        self.pomodoro_spinbox.setRange(1, 120)
        self.pomodoro_layout.addWidget(self.pomodoro_label)
        self.pomodoro_layout.addWidget(self.pomodoro_spinbox)
        self.layout.addLayout(self.pomodoro_layout)

        # Short break duration
        self.short_break_layout = QHBoxLayout()
        self.short_break_label = QLabel("Descanso Corto (minutos):")
        self.short_break_spinbox = QSpinBox()
        self.short_break_spinbox.setRange(1, 30)
        self.short_break_layout.addWidget(self.short_break_label)
        self.short_break_layout.addWidget(self.short_break_spinbox)
        self.layout.addLayout(self.short_break_layout)

        # Long break duration
        self.long_break_layout = QHBoxLayout()
        self.long_break_label = QLabel("Descanso Largo (minutos):")
        self.long_break_spinbox = QSpinBox()
        self.long_break_spinbox.setRange(1, 60)
        self.long_break_layout.addWidget(self.long_break_label)
        self.long_break_layout.addWidget(self.long_break_spinbox)
        self.layout.addLayout(self.long_break_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.save_settings)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.load_settings()

    def load_settings(self):
        pomodoro_duration = settings_manager.get_setting('pomodoro_duration')
        short_break_duration = settings_manager.get_setting('short_break_duration')
        long_break_duration = settings_manager.get_setting('long_break_duration')

        self.pomodoro_spinbox.setValue(int(pomodoro_duration) if pomodoro_duration else 25)
        self.short_break_spinbox.setValue(int(short_break_duration) if short_break_duration else 5)
        self.long_break_spinbox.setValue(int(long_break_duration) if long_break_duration else 15)

    def save_settings(self):
        settings_manager.set_setting('pomodoro_duration', self.pomodoro_spinbox.value())
        settings_manager.set_setting('short_break_duration', self.short_break_spinbox.value())
        settings_manager.set_setting('long_break_duration', self.long_break_spinbox.value())
        self.accept()
