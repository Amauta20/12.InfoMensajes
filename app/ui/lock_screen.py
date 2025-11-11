from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout
from PyQt6.QtCore import Qt
from app.security.app_security_manager import AppSecurityManager

class LockScreen(QDialog):
    """
    A dialog that prompts the user for the application lock password.
    It can also be used to set the initial application lock password.
    """
    def __init__(self, app_security_manager: AppSecurityManager, parent=None, is_setting_password: bool = False):
        super().__init__(parent)
        self.app_security_manager = app_security_manager
        self.is_setting_password = is_setting_password
        self.setWindowTitle("Bloqueo de Aplicación")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        self.form_layout = QFormLayout()

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.handle_action)
        self.form_layout.addRow("Contraseña:", self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.returnPressed.connect(self.handle_action)
        self.form_layout.addRow("Confirmar Contraseña:", self.confirm_password_input)
        
        self.layout.addLayout(self.form_layout)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.layout.addWidget(self.error_label)

        self.button_layout = QHBoxLayout()
        self.action_button = QPushButton("")
        self.action_button.setDefault(True)
        self.action_button.clicked.connect(self.handle_action)
        
        self.quit_button = QPushButton("Salir")
        self.quit_button.clicked.connect(self.reject)

        self.button_layout.addWidget(self.quit_button)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.action_button)
        
        self.layout.addLayout(self.button_layout)

        self._update_ui_for_mode()

    def _update_ui_for_mode(self):
        if self.is_setting_password or not self.app_security_manager.has_lock_password():
            self.setWindowTitle("Establecer Contraseña de Bloqueo")
            self.info_label.setText("Por favor, establece una contraseña para bloquear la aplicación.")
            self.action_button.setText("Establecer Contraseña")
            self.confirm_password_input.show()
            self.form_layout.labelForField(self.confirm_password_input).show()
        else:
            self.setWindowTitle("Desbloquear Aplicación")
            self.info_label.setText("Por favor, introduce tu contraseña de bloqueo para desbloquear la aplicación.")
            self.action_button.setText("Desbloquear")
            self.confirm_password_input.hide()
            self.form_layout.labelForField(self.confirm_password_input).hide()

    def handle_action(self):
        if self.is_setting_password or not self.app_security_manager.has_lock_password():
            self._set_password()
        else:
            self._try_unlock()

    def _set_password(self):
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not password or not confirm_password:
            self.error_label.setText("Las contraseñas no pueden estar vacías.")
            return

        if password != confirm_password:
            self.error_label.setText("Las contraseñas no coinciden.")
            self.password_input.selectAll()
            return
        
        self.app_security_manager.set_lock_password(password)
        self.app_security_manager.set_lock_enabled(True) # Enable lock when password is set
        QMessageBox.information(self, "Éxito", "Contraseña de bloqueo establecida correctamente.")
        self.accept()

    def _try_unlock(self):
        password = self.password_input.text()
        if not password:
            self.error_label.setText("La contraseña no puede estar vacía.")
            return

        if self.app_security_manager.verify_lock_password(password):
            self.accept()
        else:
            self.error_label.setText("Contraseña incorrecta. Por favor, inténtalo de nuevo.")
            self.password_input.selectAll()

    def exec(self):
        """
        Override exec to ensure the dialog is centered and focused.
        Returns QDialog.DialogCode.Accepted on success, QDialog.DialogCode.Rejected on failure/quit.
        """
        self.password_input.setFocus()
        return super().exec()
