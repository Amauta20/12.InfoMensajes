
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QInputDialog, QMessageBox, QListWidgetItem, QMenu, QLineEdit
from PyQt6.QtCore import Qt

from app.security.vault_manager import vault_manager

class VaultWidget(QWidget):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.layout = QVBoxLayout(self)

        self.status_label = QLabel("Bóveda Bloqueada. Por favor, desbloquéala.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unlock_button = QPushButton("Desbloquear Bóveda")
        self.unlock_button.clicked.connect(self.unlock_vault)

        self.secrets_list = QListWidget()
        self.secrets_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.secrets_list.customContextMenuRequested.connect(self.show_context_menu)
        self.add_secret_button = QPushButton("Añadir Nuevo Secreto")
        self.add_secret_button.clicked.connect(self.add_secret)

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.unlock_button)
        self.layout.addWidget(self.secrets_list)
        self.layout.addWidget(self.add_secret_button)

        self.update_ui()

    def update_ui(self):
        """Updates the UI based on whether the vault is locked or unlocked."""
        if vault_manager.is_locked(self.db_path):
            self.status_label.show()
            self.unlock_button.show()
            self.secrets_list.hide()
            self.add_secret_button.hide()
        else:
            self.status_label.hide()
            self.unlock_button.hide()
            self.secrets_list.show()
            self.add_secret_button.show()
            self.load_secrets()

    def unlock_vault(self):
        password, ok = QInputDialog.getText(self, 'Desbloquear Bóveda', 'Introduce tu contraseña maestra:', QLineEdit.EchoMode.Password)
        if ok and password:
            if vault_manager.unlock(self.db_path, password):
                QMessageBox.information(self, "Bóveda Desbloqueada", "La bóveda ha sido desbloqueada exitosamente.")
                self.update_ui()
            else:
                QMessageBox.warning(self, "Error", "Contraseña incorrecta.")

    def load_secrets(self):
        self.secrets_list.clear()
        try:
            secret_ids = vault_manager.get_all_secret_ids(self.db_path)
            for secret_id in secret_ids:
                self.secrets_list.addItem(QListWidgetItem(secret_id))
        except Exception as e:
            # Vault is likely locked, which is handled by update_ui
            pass

    def add_secret(self):
        secret_id, ok = QInputDialog.getText(self, 'Añadir Secreto', 'Nombre del secreto (ej. OPENAI_API_KEY):')
        if ok and secret_id:
            plaintext, ok = QInputDialog.getText(self, 'Añadir Secreto', f'Valor para {secret_id}:')
            if ok and plaintext:
                try:
                    vault_manager.save_secret(self.db_path, secret_id, plaintext)
                    QMessageBox.information(self, "Éxito", f"Secreto '{secret_id}' guardado de forma segura.")
                    self.load_secrets()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo guardar el secreto: {e}")

    def show_context_menu(self, pos):
        item = self.secrets_list.itemAt(pos)
        if not item: return

        secret_id = item.text()
        menu = QMenu()
        view_action = menu.addAction("Ver Secreto")
        delete_action = menu.addAction("Eliminar Secreto")
        
        action = menu.exec(self.secrets_list.mapToGlobal(pos))

        if action == view_action:
            self.view_secret(secret_id)
        elif action == delete_action:
            self.delete_secret(secret_id)

    def view_secret(self, secret_id):
        try:
            plaintext = vault_manager.get_secret(self.db_path, secret_id)
            QMessageBox.information(self, f"Secreto: {secret_id}", plaintext)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo recuperar el secreto: {e}")

    def delete_secret(self, secret_id):
        reply = QMessageBox.question(self, "Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar el secreto '{secret_id}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                vault_manager.delete_secret(self.db_path, secret_id)
                self.load_secrets()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el secreto: {e}")
