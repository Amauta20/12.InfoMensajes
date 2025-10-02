from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QFormLayout, QMessageBox, QColorDialog
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt
from app.db import settings_manager
from zoneinfo import available_timezones

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

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
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%m/%d/%Y %I:%M:%S %p",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M",
            "%m/%d/%Y %I:%M %p"
        ])
        self.form_layout.addRow(self.datetime_format_label, self.datetime_format_combo)

        # Pre-notification Offset Setting
        self.pre_notification_offset_label = QLabel("Pre-notificación (minutos antes):")
        self.pre_notification_offset_spin = QSpinBox()
        self.pre_notification_offset_spin.setMinimum(1)
        self.pre_notification_offset_spin.setMaximum(120)
        self.form_layout.addRow(self.pre_notification_offset_label, self.pre_notification_offset_spin)

        # Color settings
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

        self.save_button = QPushButton("Guardar Configuración")
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

        self.layout.addStretch(1)
        self.refresh_settings()

    def select_color(self, button, setting_key):
        color = QColorDialog.getColor(QColor(button.palette().button().color()))
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}")
            if setting_key == "todo_color":
                settings_manager.set_todo_color(color.name())
            elif setting_key == "inprogress_color":
                settings_manager.set_inprogress_color(color.name())
            elif setting_key == "done_color":
                settings_manager.set_done_color(color.name())

    def save_settings(self):
        settings_manager.set_timezone(self.timezone_combo.currentText())
        settings_manager.set_datetime_format(self.datetime_format_combo.currentText())
        settings_manager.set_pre_notification_offset(self.pre_notification_offset_spin.value())
        QMessageBox.information(self, "Configuración Guardada", "La configuración se ha guardado correctamente.")

    def refresh_settings(self):
        self.timezone_combo.setCurrentText(settings_manager.get_timezone())
        self.datetime_format_combo.setCurrentText(settings_manager.get_datetime_format())
        self.pre_notification_offset_spin.setValue(settings_manager.get_pre_notification_offset())

        todo_color = settings_manager.get_todo_color()
        self.todo_color_button.setStyleSheet(f"background-color: {todo_color}")

        inprogress_color = settings_manager.get_inprogress_color()
        self.inprogress_color_button.setStyleSheet(f"background-color: {inprogress_color}")

        done_color = settings_manager.get_done_color()
        self.done_color_button.setStyleSheet(f"background-color: {done_color}")
