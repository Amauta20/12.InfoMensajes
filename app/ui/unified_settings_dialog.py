from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QFormLayout, QMessageBox, QDialogButtonBox, QColorDialog
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from app.db.settings_manager import SettingsManager
from zoneinfo import available_timezones

class UnifiedSettingsDialog(QDialog):
    def __init__(self, settings_manager_instance, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager_instance
        self.setWindowTitle("Configuración General")
        self.layout = QVBoxLayout(self)

        self.todo_color = None
        self.inprogress_color = None
        self.done_color = None

        self.form_layout = QFormLayout()

        # Timezone Setting
        self.timezone_label = QLabel("Zona Horaria:")
        self.timezone_combo = QComboBox()
        self.timezone_combo.addItems(sorted(list(available_timezones())))
        self.form_layout.addRow(self.timezone_label, self.timezone_combo)

        # Datetime Format Setting
        self.datetime_format_label = QLabel("Formato de Fecha y Hora:")
        self.datetime_format_combo = QComboBox()
        self.datetime_format_combo.addItems([
            "%Y-%m-%d %H:%M:%S", # 2023-01-15 14:30:00
            "%d/%m/%Y %H:%M:%S", # 15/01/2023 14:30:00
            "%m/%d/%Y %I:%M:%S %p", # 01/15/2023 02:30:00 PM
            "%Y-%m-%d %H:%M",   # 2023-01-15 14:30
            "%d/%m/%Y %H:%M",   # 15/01/2023 14:30
            "%m/%d/%Y %I:%M %p"    # 01/15/2023 02:30 PM
        ])
        self.form_layout.addRow(self.datetime_format_label, self.datetime_format_combo)

        # Pre-notification Offset Settings
        self.pre_notification_days_label = QLabel("Pre-notificación (días antes):")
        self.pre_notification_days_spin = QSpinBox()
        self.pre_notification_days_spin.setRange(0, 30)
        self.form_layout.addRow(self.pre_notification_days_label, self.pre_notification_days_spin)

        self.pre_notification_hours_label = QLabel("Pre-notificación (horas antes):")
        self.pre_notification_hours_spin = QSpinBox()
        self.pre_notification_hours_spin.setRange(0, 23)
        self.form_layout.addRow(self.pre_notification_hours_label, self.pre_notification_hours_spin)

        self.pre_notification_minutes_label = QLabel("Pre-notificación (minutos antes):")
        self.pre_notification_minutes_spin = QSpinBox()
        self.pre_notification_minutes_spin.setRange(0, 59)
        self.form_layout.addRow(self.pre_notification_minutes_label, self.pre_notification_minutes_spin)

        # Pomodoro duration
        self.pomodoro_label = QLabel("Pomodoro (minutos):")
        self.pomodoro_spinbox = QSpinBox()
        self.pomodoro_spinbox.setRange(1, 120)
        self.form_layout.addRow(self.pomodoro_label, self.pomodoro_spinbox)

        # Short break duration
        self.short_break_label = QLabel("Descanso Corto (minutos):")
        self.short_break_spinbox = QSpinBox()
        self.short_break_spinbox.setRange(1, 30)
        self.form_layout.addRow(self.short_break_label, self.short_break_spinbox)

        # Long break duration
        self.long_break_label = QLabel("Descanso Largo (minutos):")
        self.long_break_spinbox = QSpinBox()
        self.long_break_spinbox.setRange(1, 60)
        self.form_layout.addRow(self.long_break_label, self.long_break_spinbox)

        # Kanban Color Settings
        self.todo_color_label = QLabel("Color 'Por Hacer':")
        self.todo_color_button = QPushButton()
        self.todo_color_button.clicked.connect(lambda: self.select_color(self.todo_color_button, "todo_color"))
        self.form_layout.addRow(self.todo_color_label, self.todo_color_button)

        self.inprogress_color_label = QLabel("Color 'En Progreso':")
        self.inprogress_color_button = QPushButton()
        self.inprogress_color_button.clicked.connect(lambda: self.select_color(self.inprogress_color_button, "inprogress_color"))
        self.form_layout.addRow(self.inprogress_color_label, self.inprogress_color_button)

        self.done_color_label = QLabel("Color 'Terminado':")
        self.done_color_button = QPushButton()
        self.done_color_button.clicked.connect(lambda: self.select_color(self.done_color_button, "done_color"))
        self.form_layout.addRow(self.done_color_label, self.done_color_button)

        self.layout.addLayout(self.form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.save_settings)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.load_settings()

    def load_settings(self):
        self.timezone_combo.setCurrentText(self.settings_manager.get_timezone())
        self.datetime_format_combo.setCurrentText(self.settings_manager.get_datetime_format())
        self.pre_notification_days_spin.setValue(self.settings_manager.get_pre_notification_offset_days())
        self.pre_notification_hours_spin.setValue(self.settings_manager.get_pre_notification_offset_hours())
        self.pre_notification_minutes_spin.setValue(self.settings_manager.get_pre_notification_offset_minutes())
        self.pomodoro_spinbox.setValue(self.settings_manager.get_pomodoro_duration())
        self.short_break_spinbox.setValue(self.settings_manager.get_short_break_duration())
        self.long_break_spinbox.setValue(self.settings_manager.get_long_break_duration())

        self.todo_color = self.settings_manager.get_todo_color()
        self.todo_color_button.setStyleSheet(f"background-color: {self.todo_color}")

        self.inprogress_color = self.settings_manager.get_inprogress_color()
        self.inprogress_color_button.setStyleSheet(f"background-color: {self.inprogress_color}")

        self.done_color = self.settings_manager.get_done_color()
        self.done_color_button.setStyleSheet(f"background-color: {self.done_color}")

    def select_color(self, button, setting_key):
        color = QColorDialog.getColor(QColor(button.palette().button().color()))
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}")
            if setting_key == "todo_color":
                self.todo_color = color.name()
            elif setting_key == "inprogress_color":
                self.inprogress_color = color.name()
            elif setting_key == "done_color":
                self.done_color = color.name()

    def save_settings(self):
        self.settings_manager.set_timezone(self.timezone_combo.currentText())
        self.settings_manager.set_datetime_format(self.datetime_format_combo.currentText())
        self.settings_manager.set_pre_notification_offset_days(self.pre_notification_days_spin.value())
        self.settings_manager.set_pre_notification_offset_hours(self.pre_notification_hours_spin.value())
        self.settings_manager.set_pre_notification_offset_minutes(self.pre_notification_minutes_spin.value())
        self.settings_manager.set_pomodoro_duration(self.pomodoro_spinbox.value())
        self.settings_manager.set_short_break_duration(self.short_break_spinbox.value())
        self.settings_manager.set_long_break_duration(self.long_break_spinbox.value())

        if self.todo_color:
            self.settings_manager.set_todo_color(self.todo_color)
        if self.inprogress_color:
            self.settings_manager.set_inprogress_color(self.inprogress_color)
        if self.done_color:
            self.settings_manager.set_done_color(self.done_color)

        self.accept()
