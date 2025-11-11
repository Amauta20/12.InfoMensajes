from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QFormLayout, QMessageBox, QDialogButtonBox, QColorDialog, QCheckBox, QLineEdit
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from app.db.settings_manager import SettingsManager
from app.security.vault_manager import VaultManager
from app.security.app_security_manager import AppSecurityManager
from app.ui.change_password_dialog import ChangePasswordDialog
from app.ui.lock_screen import LockScreen # Reusing LockScreen for app lock
from zoneinfo import available_timezones

class UnifiedSettingsDialog(QDialog):
    def __init__(self, settings_manager_instance, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager_instance
        self.db_connection = self.settings_manager.conn
        self.app_security_manager = AppSecurityManager(self.settings_manager) # Instantiate AppSecurityManager
        self.vault_manager = VaultManager(self.db_connection) # Instantiate VaultManager
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

        # --- AI Settings ---
        self.ai_provider_label = QLabel("Proveedor de IA:")
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(["", "OpenAI"]) # "" for None
        self.form_layout.addRow(self.ai_provider_label, self.ai_provider_combo)

        self.api_key_label = QLabel("Clave de API:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow(self.api_key_label, self.api_key_input)

        self.save_api_key_button = QPushButton("Guardar Clave de API en la Bóveda")
        self.save_api_key_button.clicked.connect(self.save_api_key_to_vault)
        self.form_layout.addRow(self.save_api_key_button)
        # --- End AI Settings ---

        self.layout.addLayout(self.form_layout)

        # --- Application Lock Settings ---
        self.app_lock_checkbox = QCheckBox("Habilitar Bloqueo de Aplicación")
        self.app_lock_checkbox.stateChanged.connect(self._toggle_app_lock)
        self.layout.addWidget(self.app_lock_checkbox)

        self.set_app_lock_password_button = QPushButton("Establecer/Cambiar Contraseña de Bloqueo")
        self.set_app_lock_password_button.clicked.connect(self._set_app_lock_password)
        self.layout.addWidget(self.set_app_lock_password_button)

        self.disable_app_lock_password_button = QPushButton("Desactivar Contraseña de Bloqueo")
        self.disable_app_lock_password_button.clicked.connect(self._disable_app_lock_password)
        self.layout.addWidget(self.disable_app_lock_password_button)
        # --- End Application Lock Settings ---

        # Change Vault Password Button
        self.change_password_button = QPushButton("Cambiar Contraseña de la Bóveda")
        self.change_password_button.clicked.connect(self.open_change_password_dialog)
        self.layout.addWidget(self.change_password_button)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.save_settings)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.load_settings()
        self._update_app_lock_ui_state() # Initial state update

    def _update_app_lock_ui_state(self):
        is_enabled = self.app_lock_checkbox.isChecked()
        has_password = self.app_security_manager.has_lock_password()

        self.set_app_lock_password_button.setEnabled(is_enabled)
        self.disable_app_lock_password_button.setEnabled(is_enabled and has_password)
        
        if not is_enabled:
            self.set_app_lock_password_button.setText("Establecer Contraseña de Bloqueo")
        elif has_password:
            self.set_app_lock_password_button.setText("Cambiar Contraseña de Bloqueo")
        else:
            self.set_app_lock_password_button.setText("Establecer Contraseña de Bloqueo")

    def _toggle_app_lock(self, state):
        enabled = bool(state)
        self.app_security_manager.set_lock_enabled(enabled)
        self._update_app_lock_ui_state()
        if enabled and not self.app_security_manager.has_lock_password():
            QMessageBox.information(self, "Bloqueo de Aplicación", "Por favor, establece una contraseña para el bloqueo de la aplicación.")
            self._set_app_lock_password()

    def _set_app_lock_password(self):
        dialog = LockScreen(self.app_security_manager, self, is_setting_password=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._update_app_lock_ui_state()

    def _disable_app_lock_password(self):
        if not self.app_security_manager.has_lock_password():
            QMessageBox.information(self, "Bloqueo de Aplicación", "No hay contraseña de bloqueo establecida para desactivar.")
            return

        # Verify current password before disabling
        verify_dialog = LockScreen(self.app_security_manager, self)
        verify_dialog.setWindowTitle("Confirmar Contraseña Actual")
        verify_dialog.info_label.setText("Introduce tu contraseña actual para desactivar el bloqueo.")
        if verify_dialog.exec() == QDialog.DialogCode.Accepted:
            reply = QMessageBox.question(self, "Desactivar Bloqueo", 
                                         "¿Estás seguro de que quieres desactivar la contraseña de bloqueo de la aplicación? Esto eliminará la contraseña.",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.app_security_manager.set_lock_password("") # Clear the hash
                self.app_security_manager.set_lock_enabled(False)
                QMessageBox.information(self, "Bloqueo de Aplicación", "Contraseña de bloqueo desactivada correctamente.")
                self._update_app_lock_ui_state()
        else:
            QMessageBox.warning(self, "Desactivar Bloqueo", "Contraseña incorrecta. No se desactivó el bloqueo.")


    def open_change_password_dialog(self):
        try:
            # Re-instantiate VaultManager to ensure it's fresh, though not strictly necessary if state is managed well
            vault_manager = VaultManager(self.db_connection)
            dialog = ChangePasswordDialog(vault_manager, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el diálogo de cambio de contraseña: {e}")

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
        
        # Load app lock settings
        self.app_lock_checkbox.setChecked(self.app_security_manager.is_lock_enabled())
        self._update_app_lock_ui_state() # Update button states based on loaded settings

        # Load AI settings
        self.ai_provider_combo.setCurrentText(self.settings_manager.get_ai_provider() or "")
        # Check if the key exists in the vault and update placeholder text
        if self.vault_manager.is_locked():
            self.api_key_input.setPlaceholderText("La bóveda está bloqueada. Desbloquéala para gestionar la clave.")
            self.api_key_input.setEnabled(False)
            self.save_api_key_button.setEnabled(False)
        else:
            try:
                provider = self.settings_manager.get_ai_provider()
                if provider:
                    secret_id = f"ai_api_key_{provider.lower()}"
                    # A simple way to check for existence without getting the value
                    if secret_id in self.vault_manager.get_all_secret_ids():
                        self.api_key_input.setPlaceholderText("Clave de API guardada en la bóveda.")
            except PermissionError:
                 # This case should be covered by is_locked, but as a safeguard
                self.api_key_input.setPlaceholderText("La bóveda está bloqueada.")
                self.api_key_input.setEnabled(False)
                self.save_api_key_button.setEnabled(False)


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

    def save_api_key_to_vault(self):
        provider = self.ai_provider_combo.currentText()
        api_key = self.api_key_input.text()

        if not provider:
            QMessageBox.warning(self, "Proveedor no seleccionado", "Por favor, selecciona un proveedor de IA antes de guardar la clave.")
            return

        if not api_key:
            QMessageBox.warning(self, "Clave de API vacía", "Por favor, introduce una clave de API.")
            return

        if self.vault_manager.is_locked():
            QMessageBox.critical(self, "Bóveda Bloqueada", "La bóveda está bloqueada. Debes desbloquearla primero.")
            return
        
        try:
            secret_id = f"ai_api_key_{provider.lower()}"
            self.vault_manager.save_secret(secret_id, api_key)
            QMessageBox.information(self, "Éxito", f"La clave de API para {provider} ha sido guardada de forma segura en la bóveda.")
            self.api_key_input.clear()
            self.api_key_input.setPlaceholderText("Clave de API guardada en la bóveda.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar la clave de API en la bóveda: {e}")

    def save_settings(self):
        try:
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
            
            # Save AI provider setting
            self.settings_manager.set_ai_provider(self.ai_provider_combo.currentText())

            # App lock settings are saved immediately by their respective methods,
            # but ensure the enabled state is consistent.
            self.app_security_manager.set_lock_enabled(self.app_lock_checkbox.isChecked())

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar Configuración", f"Ocurrió un error al guardar la configuración: {e}")
