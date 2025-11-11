from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QFormLayout, QLabel

class ChangePasswordDialog(QDialog):
    def __init__(self, vault_manager, parent=None):
        super().__init__(parent)
        self.vault_manager = vault_manager
        self.setWindowTitle("Cambiar Contraseña")
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow(QLabel("Contraseña Actual:"), self.current_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow(QLabel("Nueva Contraseña:"), self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow(QLabel("Confirmar Nueva Contraseña:"), self.confirm_password_input)

        self.layout.addLayout(self.form_layout)

        self.change_button = QPushButton("Cambiar Contraseña")
        self.change_button.clicked.connect(self.change_password)
        self.layout.addWidget(self.change_button)

    def change_password(self):
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not current_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor, rellene todos los campos.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "La nueva contraseña y la confirmación no coinciden.")
            return

        # Verify the current password
        if not self.vault_manager.unlock(current_password):
            QMessageBox.warning(self, "Error", "La contraseña actual es incorrecta.")
            return

        # Change the master passphrase
        try:
            self.vault_manager.change_master_passphrase(current_password, new_password)
            QMessageBox.information(self, "Éxito", "La contraseña se ha cambiado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cambiar la contraseña: {e}")
            self.reject()
